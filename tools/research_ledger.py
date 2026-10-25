"""CLI for explicit research events; never launches a model or publishes to Git."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research_ledger import Ledger


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default="chess_data/research_metrics.sqlite")
    actions = parser.add_subparsers(dest="action", required=True)
    create = actions.add_parser("create")
    create.add_argument("manifest", type=Path)
    record = actions.add_parser("record")
    record.add_argument("run_id")
    record.add_argument("event", type=Path)
    actions.add_parser("verify")
    export = actions.add_parser("export")
    export.add_argument("destination", type=Path)
    export.add_argument("--release", type=Path)
    args = parser.parse_args()
    with Ledger(args.database) as ledger:
        if args.action == "create":
            result = {"manifest_sha256": ledger.create_run(json.loads(args.manifest.read_text()))}
        elif args.action == "record":
            result = {"event_sha256": ledger.record(args.run_id, **json.loads(args.event.read_text()))}
        elif args.action == "verify":
            runs = ledger.snapshot()
            result = {"runs": len(runs), "events": sum(len(r["events"]) for r in runs), "integrity": "pass"}
        else:
            release = json.loads(args.release.read_text()) if args.release else None
            result = {"export": str(ledger.export(args.destination, release=release))}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
