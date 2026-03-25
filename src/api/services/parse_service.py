"""Batch parse service — reads jurisdiction.json and parses all repos."""
from __future__ import annotations

import sys
import threading
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from orchestrator.models import JavaFinding, XsltFinding  # noqa: E402
from orchestrator.parsers.java_parser import JavaParser  # noqa: E402
from orchestrator.parsers.xslt_parser import XsltParser  # noqa: E402
from orchestrator.scanner import ModuleScanner  # noqa: E402
from orchestrator.stitcher import Stitcher  # noqa: E402

from ..schemas.jurisdiction import JurisdictionConfig  # noqa: E402
from .cache import JurisdictionCache, parse_cache  # noqa: E402
from .xpath_service import XPathIndex  # noqa: E402


def parse_jurisdiction(config: JurisdictionConfig) -> JurisdictionCache:
    """Parse a single jurisdiction's repos and build lineage."""
    cache = JurisdictionCache(jurisdiction_id=config.id, status="parsing")
    parse_cache.set(config.id, cache)
    parse_cache.add_log("info", f"Starting parse for {config.name}", config.id)

    java_findings: list[JavaFinding] = []
    xslt_findings: list[XsltFinding] = []

    git_path = Path(config.git_path)
    lib_path = Path(config.lib_path)

    java_parser = JavaParser(repo_name=config.id)
    xslt_parser = XsltParser(repo_name=config.id)
    scanner = ModuleScanner()

    # Parse main repo
    for repo_path in [git_path, lib_path]:
        if not repo_path.exists():
            parse_cache.add_log(
                "warn",
                f"Repo path not found: {repo_path}, skipping",
                config.id,
            )
            continue

        parse_cache.add_log("info", f"Scanning {repo_path}", config.id)
        try:
            project = scanner.scan_project(repo_path, name=config.id)
            for module in project.modules:
                for java_file in module.java_files:
                    try:
                        findings = java_parser.parse_file(java_file)
                        java_findings.extend(findings)
                        parse_cache.add_log(
                            "debug",
                            f"Parsed {java_file.name}: {len(findings)} findings",
                            config.id,
                        )
                    except Exception as e:
                        parse_cache.add_log(
                            "error", f"Error parsing {java_file}: {e}", config.id
                        )

                for xslt_file in module.xslt_files:
                    try:
                        findings = xslt_parser.parse_file(xslt_file)
                        xslt_findings.extend(findings)
                        parse_cache.add_log(
                            "debug",
                            f"Parsed {xslt_file.name}: {len(findings)} findings",
                            config.id,
                        )
                    except Exception as e:
                        parse_cache.add_log(
                            "error", f"Error parsing {xslt_file}: {e}", config.id
                        )
        except Exception as e:
            parse_cache.add_log(
                "warn", f"Could not scan project at {repo_path}: {e}", config.id
            )

    # Stitch
    parse_cache.add_log(
        "info",
        f"Stitching {len(java_findings)} Java + {len(xslt_findings)} XSLT findings",
        config.id,
    )
    stitcher = Stitcher()
    lineage = stitcher.stitch(java_findings, xslt_findings)

    # Build XPath index
    xpath_index = XPathIndex()
    xpath_index.build_from_findings(xslt_findings)

    # Update cache
    cache.java_findings = java_findings
    cache.xslt_findings = xslt_findings
    cache.lineage = lineage
    cache.xpath_index = xpath_index
    cache.parsed_at = datetime.now()
    cache.status = "ready"
    parse_cache.set(config.id, cache)

    parse_cache.add_log(
        "info",
        f"Parse complete for {config.name}: "
        f"{len(lineage.nodes)} nodes, {len(lineage.edges)} edges",
        config.id,
    )
    return cache


def parse_all(jurisdictions: list[JurisdictionConfig]):
    """Parse all jurisdictions (runs in background thread)."""
    parse_cache.batch_status = "running"
    parse_cache.batch_started = datetime.now()
    parse_cache.add_log("info", "Batch parse started")

    for config in jurisdictions:
        try:
            parse_jurisdiction(config)
        except Exception as e:
            parse_cache.add_log("error", f"Failed to parse {config.id}: {e}", config.id)
            cache = JurisdictionCache(
                jurisdiction_id=config.id, status="error", error=str(e)
            )
            parse_cache.set(config.id, cache)

    parse_cache.batch_status = "done"
    parse_cache.batch_completed = datetime.now()
    parse_cache.add_log("info", "Batch parse completed")


def trigger_batch_parse(jurisdictions: list[JurisdictionConfig]):
    """Trigger batch parse in a background thread."""
    if parse_cache.batch_status == "running":
        return False
    thread = threading.Thread(target=parse_all, args=(jurisdictions,), daemon=True)
    thread.start()
    return True
