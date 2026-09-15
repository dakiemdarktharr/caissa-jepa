"""Explicit offline protocol execution. Never downloads data or trains models."""
import argparse
import json
from pathlib import Path
import sys
import traceback
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from confirmatory_protocol import run_protocol, gate
from runtime_safety import atomic_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args()
    if args.output.resolve() == args.protocol.resolve() or args.output.exists():
        parser.error('Output must be a new result path, separate from the protocol')
    protocol = json.loads(args.protocol.read_text(encoding='utf-8'))
    try:
        result = gate(protocol) if args.validate_only else run_protocol(protocol)
    except Exception as error:
        result = {'status': 'FAILED', 'ranking_ready': False, 'error': repr(error), 'traceback': traceback.format_exc()}
    atomic_json(args.output, {'research_name': 'MARS-JEPA Chess', 'protocol': protocol, 'result': result})
    return 0 if result.get('protocol_ready') or result.get('ranking_ready') else 1


if __name__ == '__main__':
    raise SystemExit(main())
