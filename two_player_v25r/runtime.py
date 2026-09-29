"""Fresh V2.5 grid runner with the amended, bounded-memory RSS monitor.

Usage: python -m two_player_v25r.runtime TRAIN DEVELOPMENT NEW_GRID_OUTPUT
No scientific setting, budget, data path or fresh-only rule is overridden.
"""
import json

from .bindings import original_runtime, repaired_bindings


def run_grid(training, development, output):
    with repaired_bindings():
        return original_runtime.run_grid(training, development, output)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('training'); parser.add_argument('development'); parser.add_argument('output')
    args = parser.parse_args()
    result = run_grid(args.training, args.development, args.output)
    print(json.dumps({'status': result['status'],
                      'complete': sum(r['status'] == 'complete' for r in result['runs']),
                      'failures': result['failures']}))
    return 0 if result['status'] == 'complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
