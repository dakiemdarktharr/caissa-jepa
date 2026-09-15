"""Audit, derive or plan a CAISSA dataset without changing the raw source."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataset_integrity import inspect_dataset, derive_dataset
from research_protocol import build_split_plan
from runtime_safety import atomic_json

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('audit', 'derive', 'split', 'research-audit'))
    parser.add_argument('dataset', type=Path)
    parser.add_argument('output', type=Path, help='New dataset/plan directory, or external audit receipt JSON')
    args = parser.parse_args()
    source, output = args.dataset.resolve(strict=True), args.output.resolve()
    if source == output or source in output.parents:
        parser.error('Output must be outside the input dataset')
    if args.operation == 'research-audit':
        from research_dataset import publish_audit
        result = publish_audit(source, output)
    elif args.operation == 'audit':
        result = inspect_dataset(source)
        atomic_json(output, result)
    elif args.operation == 'derive':
        result = derive_dataset(source, output)
    else:
        result = build_split_plan(source, output)
    print(json.dumps({k: v for k, v in result.items() if k not in ('shards', 'assignments')}, indent=2))
    return 1 if result.get('status') == 'FAILED' else 0

if __name__ == '__main__':
    raise SystemExit(main())
