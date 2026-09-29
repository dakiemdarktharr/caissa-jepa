"""Strict original V2.5 report with the same amended source identity as fitting.

Usage: python -m two_player_v25r.report COMPLETED_GRID NEW_REPORT_DIRECTORY
Only delegates the original saved-artifact verifier; no model predictions.
"""
import json
from pathlib import Path

from two_player_v25 import report as original_report
from .bindings import repaired_bindings

markdown = original_report.markdown


def summarize_grid(directory):
    with repaired_bindings():
        return original_report.summarize_grid(directory)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('grid'); parser.add_argument('output')
    args = parser.parse_args()
    result = summarize_grid(args.grid)
    output = Path(args.output); output.mkdir(parents=True, exist_ok=False)
    (output/'report.json').write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
    (output/'report.md').write_text(markdown(result), encoding='utf-8')
    print(json.dumps({'status': result['status'], 'errors': len(result['verification_errors']),
                      'output': str(output.resolve())}))
    return 1 if result['verification_errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
