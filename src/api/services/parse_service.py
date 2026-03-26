"""Batch parse service — reads jurisdiction.json and parses all repos."""
from __future__ import annotations

import logging
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

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
    t_start = time.perf_counter()
    logger.info("parse_jurisdiction: starting '%s' (%s)", config.id, config.name)
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
            logger.debug(
                "[%s] Scanned %s: %d modules, %d Java files, %d XSLT files",
                config.id, repo_path,
                len(project.modules),
                sum(len(m.java_files) for m in project.modules),
                sum(len(m.xslt_files) for m in project.modules),
            )
            for module in project.modules:
                for java_file in module.java_files:
                    try:
                        findings = java_parser.parse_file(java_file)
                        java_findings.extend(findings)
                        parse_cache.add_log(
                            "debug",
                            f"Parsed {java_file.name}: {len(findings)} Java findings",
                            config.id,
                        )
                    except Exception as e:
                        logger.exception(
                            "[%s] Error parsing Java file %s", config.id, java_file
                        )
                        parse_cache.add_log(
                            "error", f"Error parsing {java_file}: {e}", config.id
                        )

                for xslt_file in module.xslt_files:
                    try:
                        findings = xslt_parser.parse_file(xslt_file)
                        xslt_findings.extend(findings)
                        parse_cache.add_log(
                            "debug",
                            f"Parsed {xslt_file.name}: {len(findings)} XSLT findings",
                            config.id,
                        )
                    except Exception as e:
                        logger.exception(
                            "[%s] Error parsing XSLT file %s", config.id, xslt_file
                        )
                        parse_cache.add_log(
                            "error", f"Error parsing {xslt_file}: {e}", config.id
                        )
        except Exception as e:
            logger.warning(
                "[%s] Could not scan project at %s: %s", config.id, repo_path, e
            )
            parse_cache.add_log(
                "warn", f"Could not scan project at {repo_path}: {e}", config.id
            )

    # Stitch
    logger.info(
        "[%s] Stitching %d Java + %d XSLT findings",
        config.id, len(java_findings), len(xslt_findings),
    )
    parse_cache.add_log(
        "info",
        f"Stitching {len(java_findings)} Java + {len(xslt_findings)} XSLT findings",
        config.id,
    )
    t_stitch = time.perf_counter()
    stitcher = Stitcher()
    lineage = stitcher.stitch(java_findings, xslt_findings)
    logger.info(
        "[%s] Stitching complete in %.1fs — %d nodes, %d edges",
        config.id, time.perf_counter() - t_stitch,
        len(lineage.nodes), len(lineage.edges),
    )

    # Build XPath index
    xpath_index = XPathIndex()
    xpath_index.build_from_findings(xslt_findings)
    logger.debug("[%s] XPath index built from %d XSLT findings", config.id, len(xslt_findings))

    # Update cache
    cache.java_findings = java_findings
    cache.xslt_findings = xslt_findings
    cache.lineage = lineage
    cache.xpath_index = xpath_index
    cache.parsed_at = datetime.now()
    cache.status = "ready"
    parse_cache.set(config.id, cache)

    elapsed = time.perf_counter() - t_start
    parse_cache.add_log(
        "info",
        f"Parse complete for {config.name}: "
        f"{len(lineage.nodes)} nodes, {len(lineage.edges)} edges "
        f"(took {elapsed:.1f}s)",
        config.id,
    )
    logger.info(
        "parse_jurisdiction: '%s' finished in %.1fs — "
        "%d Java findings, %d XSLT findings, %d nodes, %d edges",
        config.id, elapsed,
        len(java_findings), len(xslt_findings),
        len(lineage.nodes), len(lineage.edges),
    )
    return cache


def parse_all(jurisdictions: list[JurisdictionConfig]):
    """Parse all jurisdictions (runs in background thread)."""
    t_batch = time.perf_counter()
    logger.info(
        "Batch parse started — %d jurisdiction(s): %s",
        len(jurisdictions), [j.id for j in jurisdictions],
    )
    parse_cache.batch_status = "running"
    parse_cache.batch_started = datetime.now()
    parse_cache.add_log("info", f"Batch parse started ({len(jurisdictions)} jurisdictions)")

    errors: list[str] = []
    for config in jurisdictions:
        try:
            parse_jurisdiction(config)
        except Exception as e:
            logger.exception("Batch parse: unhandled error for jurisdiction '%s'", config.id)
            parse_cache.add_log("error", f"Failed to parse {config.id}: {e}", config.id)
            cache = JurisdictionCache(
                jurisdiction_id=config.id, status="error", error=str(e)
            )
            parse_cache.set(config.id, cache)
            errors.append(config.id)

    parse_cache.batch_status = "done"
    parse_cache.batch_completed = datetime.now()
    elapsed = time.perf_counter() - t_batch

    if errors:
        logger.warning(
            "Batch parse completed in %.1fs with %d error(s): %s",
            elapsed, len(errors), errors,
        )
        parse_cache.add_log(
            "warn",
            f"Batch parse completed in {elapsed:.1f}s — {len(errors)} error(s): {errors}",
        )
    else:
        logger.info("Batch parse completed in %.1fs — all jurisdictions ready", elapsed)
        parse_cache.add_log("info", f"Batch parse completed in {elapsed:.1f}s")


def trigger_batch_parse(jurisdictions: list[JurisdictionConfig]):
    """Trigger batch parse in a background thread."""
    if parse_cache.batch_status == "running":
        logger.warning("trigger_batch_parse: parse already running, ignoring request")
        return False
    logger.info(
        "trigger_batch_parse: launching background thread for %d jurisdiction(s)",
        len(jurisdictions),
    )
    thread = threading.Thread(target=parse_all, args=(jurisdictions,), daemon=True)
    thread.start()
    return True
