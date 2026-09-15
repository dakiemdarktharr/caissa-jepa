"""Read-only dataset audit; writes only the explicitly selected report file."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_safety import atomic_json


def audit(root):
    root = Path(root).resolve(strict=True)
    manifest_bytes = (root / 'dataset_manifest.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    seen, duplicates, shards, invalid = {}, [], [], []
    games = positions = byte_count = 0
    splits, results = Counter(), Counter()
    for item in manifest['shards']:
        path = (root / item['path']).resolve(strict=True)
        if root not in path.parents:
            raise ValueError('Shard escapes dataset root')
        digest = hashlib.sha256()
        n = p = size = 0
        with path.open('rb') as handle:
            for line_number, raw in enumerate(handle, 1):
                digest.update(raw)
                size += len(raw)
                row = json.loads(raw)
                key = row['game_hash']
                location = {'shard': item['path'], 'line': line_number}
                # Compare content excluding source provenance for repeated hashes.
                canonical = dict(row)
                canonical.pop('source', None)
                content_hash = hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()
                if key in seen:
                    original, original_content = seen[key]
                    duplicates.append({'game_hash': key, 'first': original,
                                       'repeat': location, 'same_content_except_source': content_hash == original_content})
                else:
                    seen[key] = (location, content_hash)
                split = 'validation' if int(key[:8], 16) % 100 < 10 else 'train'
                splits[split] += 1
                results[str(row.get('headers', {}).get('Result'))] += 1
                if not isinstance(row.get('positions'), list):
                    invalid.append(location)
                    continue
                n += 1
                p += len(row['positions'])
        shards.append({'path': item['path'], 'games': n, 'positions': p, 'bytes': size,
                       'hash_matches': digest.hexdigest() == item['sha256'],
                       'size_matches': size == item['bytes']})
        games += n
        positions += p
        byte_count += size
        print(json.dumps(shards[-1]), flush=True)
    actual = {'games': games, 'positions': positions, 'written_bytes': byte_count}
    mismatches = {k: {'manifest': manifest.get(k), 'actual': v}
                  for k, v in actual.items() if manifest.get(k) != v}
    listed = {s['path'] for s in manifest['shards']}
    unlisted = [p.relative_to(root).as_posix() for p in root.glob('shards/*.jsonl')
                if p.relative_to(root).as_posix() not in listed]
    # Probe the existing reconciliation decision without constructing a writer.
    from fen_dataset_tool import ShardedDatasetWriter
    writer = ShardedDatasetWriter.__new__(ShardedDatasetWriter)
    writer.output_dir, writer.shard_dir, writer.manifest = root, root / 'shards', manifest
    writer.current_shard = int(manifest.get('current_shard', 1))
    reconcile_requested = writer._needs_reconciliation()
    if (root / 'dataset_manifest.json').read_bytes() != manifest_bytes:
        raise RuntimeError('Dataset manifest changed during audit')
    return {'captured_at': datetime.now(timezone.utc).isoformat(), 'dataset': str(root),
            'manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest(),
            'actual': actual, 'manifest_mismatches': mismatches,
            'unique_game_hashes': len(seen), 'duplicate_rows': len(duplicates),
            'duplicate_percent': 100 * len(duplicates) / max(1, games),
            'duplicates': duplicates, 'shards': shards, 'unlisted_shards': unlisted,
            'invalid_position_lists': invalid, 'game_split_counts_10_percent': dict(splits),
            'result_counts': dict(results), 'existing_writer_requests_reconciliation': reconcile_requested,
            'scope': 'All listed JSONL records; no full legal replay or position-level leakage audit'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset')
    parser.add_argument('--report', required=True)
    parser.add_argument('--research', action='store_true', help='Version-2 full-FEN audit and locked disjoint split plan')
    args = parser.parse_args()
    dataset = Path(args.dataset).resolve(strict=True)
    report = Path(args.report).resolve()
    if report == dataset or dataset in report.parents:
        parser.error('Report must be outside the input dataset')
    from research_dataset import audit_dataset
    result = audit_dataset(dataset) if args.research else audit(dataset)
    atomic_json(report, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('shards', 'duplicates')}))
