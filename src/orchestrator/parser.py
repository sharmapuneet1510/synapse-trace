"""Main orchestrator — coordinates scanning, parsing, stitching, and graph persistence.

Supports four input modes:
  1. --project DIRS     Auto-discover modules within each project root (multi-module)
  2. --scan DIRS        Auto-discover .java and .xsl/.xslt files in each directory
  3. --config FILE      JSON config with repos (project_scan, scan_dirs, or java_dirs/xslt_dirs)
  4. --java-dirs/--xslt-dirs  Legacy explicit separation
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

from orchestrator.models import RepoConfig, StitchedLineage
from orchestrator.parsers.java_parser import JavaParser
from orchestrator.parsers.xslt_parser import XsltParser
from orchestrator.scanner import ModuleScanner, ScannedModule
from orchestrator.stitcher import Stitcher
from orchestrator.storage.base_provider import BaseGraphProvider
from orchestrator.storage.local_graph_pyvis import PyVisGraphProvider
from orchestrator.storage.neo4j_adapter import Neo4jGraphProvider

STORAGE_REGISTRY: dict[str, type[BaseGraphProvider]] = {
    "pyvis": PyVisGraphProvider,
    "neo4j": Neo4jGraphProvider,
}


@dataclass
class SynapseConfig:
    """Configuration for a Synapse Trace run."""

    repos: list[RepoConfig] = field(default_factory=list)
    target_storages: list[str] = field(default_factory=lambda: ["pyvis"])
    output_dir: Path = Path("output")
    neo4j_uri: str = ""
    neo4j_user: str = ""
    neo4j_password: str = ""

    # Legacy single-repo fields (converted to repos in __post_init__)
    java_source_dirs: list[Path] = field(default_factory=list)
    xslt_source_dirs: list[Path] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.repos and (self.java_source_dirs or self.xslt_source_dirs):
            self.repos.append(
                RepoConfig(
                    name="default",
                    path=Path("."),
                    java_dirs=list(self.java_source_dirs),
                    xslt_dirs=list(self.xslt_source_dirs),
                )
            )


class SynapseTracer:
    """Orchestrates the scan -> parse -> stitch -> persist pipeline."""

    def __init__(self, config: SynapseConfig) -> None:
        self._config = config
        self._scanner = ModuleScanner()
        self._stitcher = Stitcher()
        self._providers = self._init_providers()

    def _init_providers(self) -> list[BaseGraphProvider]:
        providers: list[BaseGraphProvider] = []
        for name in self._config.target_storages:
            if name not in STORAGE_REGISTRY:
                print(f"Warning: unknown storage provider '{name}', skipping.")
                continue
            cls = STORAGE_REGISTRY[name]
            if name == "pyvis":
                providers.append(cls(output_dir=self._config.output_dir))
            elif name == "neo4j":
                providers.append(
                    cls(
                        uri=self._config.neo4j_uri,
                        user=self._config.neo4j_user,
                        password=self._config.neo4j_password,
                    )
                )
        return providers

    def _parse_module(
        self,
        module: ScannedModule,
        java_parser: JavaParser,
        xslt_parser: XsltParser,
        all_java_findings: list,
        all_xslt_findings: list,
        indent: str = "    ",
    ) -> None:
        """Parse all files in a scanned module and append findings."""
        for java_file in module.java_files:
            findings = java_parser.parse_file(java_file)
            all_java_findings.extend(findings)

        for xslt_file in module.xslt_files:
            findings = xslt_parser.parse_file(xslt_file)
            all_xslt_findings.extend(findings)

        if module.xslt_refs:
            print(f"{indent}Cross-language refs:")
            for ref in module.xslt_refs:
                resolved = ref.xslt_resolved or "(unresolved)"
                print(
                    f"{indent}  {ref.java_class}.{ref.java_method}() "
                    f"-> {ref.xslt_filename} [{ref.ref_type}] -> {resolved}"
                )

    def trace(self) -> StitchedLineage:
        """Run the full pipeline across all configured repos."""
        all_java_findings = []
        all_xslt_findings = []

        for repo in self._config.repos:
            repo.resolve_dirs()
            print(f"\n  Project: {repo.name} ({repo.path})")

            java_parser = JavaParser(repo_name=repo.name)
            xslt_parser = XsltParser(repo_name=repo.name)

            # --- Project scan mode: auto-discover modules ---
            if repo.project_scan:
                project = self._scanner.scan_project(repo.path, name=repo.name)
                print(f"    {project.summary()}")

                for module in project.modules:
                    print(f"    Module: {module.name} — {module.summary()}")
                    # Use module-qualified repo name for node IDs
                    mod_java = JavaParser(repo_name=module.name)
                    mod_xslt = XsltParser(repo_name=module.name)
                    self._parse_module(
                        module, mod_java, mod_xslt,
                        all_java_findings, all_xslt_findings,
                        indent="      ",
                    )

            # --- Auto-scan mode: discover files in scan_dirs ---
            if repo.scan_dirs:
                for d in repo.scan_dirs:
                    if not d.exists():
                        print(f"    Warning: scan dir not found: {d}")
                        continue

                    module = self._scanner.scan(d, name=repo.name)
                    print(f"    Scanned: {module.summary()}")
                    self._parse_module(
                        module, java_parser, xslt_parser,
                        all_java_findings, all_xslt_findings,
                    )

            # --- Explicit dirs mode: parse java_dirs and xslt_dirs ---
            for d in repo.java_dirs:
                if not d.exists():
                    print(f"    Warning: Java dir not found: {d}")
                    continue
                found = java_parser.parse_directory(d)
                all_java_findings.extend(found)
                print(f"    Java: {len(found)} findings from {d}")

            for d in repo.xslt_dirs:
                if not d.exists():
                    print(f"    Warning: XSLT dir not found: {d}")
                    continue
                found = xslt_parser.parse_directory(d)
                all_xslt_findings.extend(found)
                print(f"    XSLT: {len(found)} findings from {d}")

        # Stitch all findings across all repos
        lineage = self._stitcher.stitch(all_java_findings, all_xslt_findings)
        print(f"\n  Stitched: {len(lineage.nodes)} nodes, {len(lineage.edges)} edges")

        # Count special edges
        cross_repo = sum(1 for e in lineage.edges if e.edge_type.value == "CROSS_REPO")
        loads_xslt = sum(1 for e in lineage.edges if e.edge_type.value == "LOADS_XSLT")
        if cross_repo:
            print(f"  Cross-repo links: {cross_repo}")
        if loads_xslt:
            print(f"  Java→XSLT links: {loads_xslt}")

        # Persist
        for provider in self._providers:
            provider_name = type(provider).__name__
            provider.ingest_lineage(lineage)
            try:
                provider.persist()
                print(f"  Persisted to {provider_name}")
            except NotImplementedError as e:
                print(f"  {provider_name}: {e}")

        return lineage


def main() -> None:
    """CLI entry point for synapse-trace."""
    parser = argparse.ArgumentParser(
        description="Synapse Trace — Data Lineage Tracer for Java/XSLT codebases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Auto-discover modules in a project (recommended for multi-module):
  synapse-trace --project /path/to/project-root

  # Multiple projects:
  synapse-trace --project /path/to/project-a /path/to/project-b

  # Auto-scan a single module:
  synapse-trace --scan src/

  # Auto-scan multiple modules:
  synapse-trace --scan app/src lib/src --names app-trade lib-common

  # Multi-repo via JSON config:
  synapse-trace --config repos.json

  # Legacy explicit mode:
  synapse-trace --java-dirs src/main/java --xslt-dirs src/main/resources/xslt
        """,
    )

    # Project scan mode (recommended for multi-module)
    parser.add_argument(
        "--project", nargs="+", default=[],
        help="Project root(s) to auto-discover modules in (pom.xml, build.gradle, src/ layout)",
    )
    parser.add_argument(
        "--project-names", nargs="+", default=[],
        help="Names for each --project root (optional, defaults to dir name)",
    )

    # Auto-scan mode
    parser.add_argument(
        "--scan", nargs="+", default=[],
        help="Directories to auto-scan for .java and .xsl/.xslt files",
    )
    parser.add_argument(
        "--names", nargs="+", default=[],
        help="Names for each --scan directory (optional, defaults to dir name)",
    )

    # Config file mode
    parser.add_argument(
        "--config",
        help="Path to JSON config file with repos list",
    )

    # Legacy repo mode
    parser.add_argument(
        "--repo", action="append", default=[],
        help="Add a repo: NAME:PATH (can repeat)",
    )
    parser.add_argument("--java-dirs", nargs="+", default=[])
    parser.add_argument("--xslt-dirs", nargs="+", default=[])

    parser.add_argument(
        "--storages", nargs="+", default=["pyvis"],
        help="Storage providers (default: pyvis). Options: pyvis, neo4j",
    )
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--neo4j-uri", default="")
    parser.add_argument("--neo4j-user", default="")
    parser.add_argument("--neo4j-password", default="")

    args = parser.parse_args()

    repos: list[RepoConfig] = []

    if args.project:
        # Project scan mode — auto-discover modules
        for i, proj_dir in enumerate(args.project):
            name = args.project_names[i] if i < len(args.project_names) else Path(proj_dir).name
            repos.append(
                RepoConfig(
                    name=name,
                    path=Path(proj_dir),
                    project_scan=True,
                )
            )
    elif args.scan:
        # Auto-scan mode
        for i, scan_dir in enumerate(args.scan):
            name = args.names[i] if i < len(args.names) else Path(scan_dir).name
            repos.append(
                RepoConfig(
                    name=name,
                    path=Path(scan_dir),
                    scan_dirs=[Path(".")],  # scan the root itself
                )
            )
    elif args.config:
        config_data = json.loads(Path(args.config).read_text())
        for r in config_data.get("repos", []):
            repos.append(
                RepoConfig(
                    name=r["name"],
                    path=Path(r["path"]),
                    project_scan=r.get("project_scan", False),
                    scan_dirs=[Path(d) for d in r.get("scan_dirs", [])],
                    java_dirs=[Path(d) for d in r.get("java_dirs", [])],
                    xslt_dirs=[Path(d) for d in r.get("xslt_dirs", [])],
                )
            )
    elif args.repo:
        for repo_spec in args.repo:
            if ":" in repo_spec:
                name, path = repo_spec.split(":", 1)
            else:
                name, path = repo_spec, repo_spec
            repos.append(
                RepoConfig(
                    name=name,
                    path=Path(path),
                    java_dirs=[Path(d) for d in args.java_dirs],
                    xslt_dirs=[Path(d) for d in args.xslt_dirs],
                )
            )

    config = SynapseConfig(
        repos=repos,
        java_source_dirs=[Path(d) for d in args.java_dirs] if not repos else [],
        xslt_source_dirs=[Path(d) for d in args.xslt_dirs] if not repos else [],
        target_storages=args.storages,
        output_dir=Path(args.output_dir),
        neo4j_uri=args.neo4j_uri,
        neo4j_user=args.neo4j_user,
        neo4j_password=args.neo4j_password,
    )

    print("Synapse Trace — Data Lineage Analysis")
    print("=" * 50)
    print(f"  Repos/Projects: {len(config.repos)}")

    tracer = SynapseTracer(config)
    lineage = tracer.trace()

    print("=" * 50)
    print(f"Done. {len(lineage.nodes)} nodes, {len(lineage.edges)} edges traced.")


if __name__ == "__main__":
    main()
