#!/usr/bin/env python3
"""Re-index all configured repositories."""
import os
import sys
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.trace_core.indexers.repo_indexer import RepoIndexer


def main():
    cfg_path = "configs/repositories.yaml"
    if not os.path.isfile(cfg_path):
        print(f"ERROR: {cfg_path} not found")
        sys.exit(1)

    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)

    repos = [r["path"] for r in cfg.get("repositories", []) if r.get("enabled", True)]
    print(f"[SynapseTrace] Indexing {len(repos)} repositories:")
    for r in repos:
        print(f"  • {r}")

    indexer = RepoIndexer()
    index = indexer.index(repos)

    print(f"\n[Done]")
    print(f"  Java classes  : {len(index.java_classes)}")
    print(f"  XSLT templates: {len(index.xslt_templates)}")
    print(f"  Cross-links   : {len(index.cross_links)}")


if __name__ == "__main__":
    main()
