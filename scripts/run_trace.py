#!/usr/bin/env python3
"""Run a field lineage trace from the command line."""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.trace_core.tracing.trace_service import TraceService


def main():
    parser = argparse.ArgumentParser(description="Data Lineage Platform – Field Trace")
    parser.add_argument("field_name", help="Name of the field to trace (e.g. N_CLEARED)")
    parser.add_argument("--jurisdiction", default=None, help="Optional jurisdiction filter")
    parser.add_argument("--max-depth", type=int, default=20, help="Max recursion depth")
    parser.add_argument("--output-dir", default="outputs", help="Output base directory")
    parser.add_argument(
        "--format",
        choices=["json", "html", "pipeline", "branch", "neo4j"],
        default="json",
        help="Output format",
    )
    args = parser.parse_args()

    print(f"[SynapseTrace] Tracing field: {args.field_name}")
    service = TraceService()
    result = service.trace(
        field_name=args.field_name,
        jurisdiction=args.jurisdiction,
        max_depth=args.max_depth,
    )

    print(f"\nTrace ID     : {result.trace_id}")
    print(f"Field        : {result.field_name}")
    print(f"Origin       : {result.summary.origin.value}")
    print(f"Nodes        : {result.summary.total_nodes}")
    print(f"Branches     : {result.summary.branch_count}")
    print(f"Has XSLT     : {result.summary.has_xslt}")
    print(f"Has Java     : {result.summary.has_java}")
    print(f"\nPipeline Steps:")
    for step in result.summary.pipeline_steps:
        print(f"  • {step}")
    print(f"\nBusiness Explanation:\n{result.summary.business_explanation}")

    fmt = args.format
    os.makedirs(args.output_dir, exist_ok=True)

    if fmt == "json":
        out_path = os.path.join(args.output_dir, "json", f"{args.field_name}.json")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result.to_json(), f, indent=2, default=str)
        print(f"\nJSON output  : {out_path}")
    elif fmt == "html":
        out_path = os.path.join(args.output_dir, "html", f"{args.field_name}.html")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result.to_html())
        print(f"\nHTML output  : {out_path}")
    elif fmt == "pipeline":
        print("\nPipeline JSON:")
        print(json.dumps(result.to_pipeline_json(), indent=2, default=str))
    elif fmt == "branch":
        print("\nBranch JSON:")
        print(json.dumps(result.to_branch_json(), indent=2, default=str))
    elif fmt == "neo4j":
        out_path = os.path.join(args.output_dir, "json", f"{args.field_name}_neo4j.json")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result.to_neo4j(), f, indent=2, default=str)
        print(f"\nNeo4j output : {out_path}")


if __name__ == "__main__":
    main()
