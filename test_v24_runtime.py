"""Probe-runtime failure invariants; synthetic receipts and mocked measurements."""
from contextlib import ExitStack
from dataclasses import asdict
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from two_player_v24_probe import runtime as r


class V24RuntimeTests(unittest.TestCase):
    def test_real_core_report_contract_on_synthetic_legal_closures_without_fitting(self):
        from two_player_v2 import GAMES_V2
        from two_player_v2.data import closure
        from two_player_v22.model import Config, Model
        from two_player_v24_probe.core import build_schedule, measure
        from two_player_v24_probe.report import validate_schedule, validate_row
        train = {'manifest': {'split': 'train', 'role': 'redacted-training', 'fraction': 1.},
                 'roots': [], 'forks': [], 'nodes': {}}
        for name, game in GAMES_V2.items():
            first = game.initial(); second = first
            for _ in range(2): second = game.transition(second, game.legal_actions(second)[0])
            for index, state in enumerate((first, second)):
                rid = name+'-synthetic-'+str(index)
                train['roots'].append({'root_id': rid, 'game': name, 'split': 'train',
                                       'state': asdict(state), 'actions': list(game.legal_actions(state))})
                nodes, forks, _ = closure(name, state)
                for nid, position in nodes.items():
                    outcome = game.terminal(position)
                    train['nodes'][nid] = {'game': name, 'state': asdict(position),
                        'value': 0 if outcome is None else outcome*position.player,
                        'value_labelled': True, 'terminal': outcome is not None,
                        'legal': list(game.legal_actions(position))}
                train['forks'].extend({'root_id': rid, 'game': name, 'split': 'train',
                                       'node_ids': ids, 'actions': actions} for ids, actions in forks)
        schedule = build_schedule(train, lambda: None)
        counts = validate_schedule(schedule)
        self.assertGreater(sum(c['blocks'] for c in counts.values()), 0)
        for variant in ('direct', 'value-dynamics', 'raw-jepa'):
            config = Config(variant=variant, seed=17, jepa_weight=.1 if variant == 'raw-jepa' else 1.)
            model = Model(config)
            result = measure(model, train, schedule, lambda: None)
            self.assertEqual(len(result['rows']), 4)
            for row in result['rows']: validate_row(row, counts[row['game']])
            self.assertEqual((model.epoch, model.step), (0, 0))

    def fixture(self, stack, directory):
        """No real checkpoint, research dataset, encoding or optimizer is accessed."""
        root = Path(directory); grid = root/'grid'; trainpath = root/'train'; output = root/'probe'
        grid.mkdir(); trainpath.mkdir()
        source = {'fixture.py': 'a'*64}
        manifest = {'dataset_fingerprint': r.DATA_FINGERPRINT, 'split': 'train',
                    'role': 'redacted-training', 'fraction': 1.}
        r.atomic_json(trainpath/'manifest.json', manifest)
        r.atomic_json(trainpath/'data.json', {'fixture': 'not a research dataset'})
        configs = r.configurations(); cells = []
        for config in configs:
            name = r.run_id(config); cell = grid/name; cell.mkdir()
            (cell/'checkpoint-e160.npz').write_bytes(b'Engineering fixture; Model.load is mocked.')
            receipt = {'identity': {'fixture': True}, 'snapshots': [{'epoch': 160,
                'checkpoint': 'checkpoint-e160.npz', 'checkpoint_sha256': r.sha(cell/'checkpoint-e160.npz')}]}
            r.atomic_json(cell/'receipt.json', receipt)
            cells.append({'id': name, 'config': asdict(config), 'status': 'complete',
                          'receipt_sha256': r.sha(cell/'receipt.json')})
        ledger = {'status': 'complete', 'failures': [], 'code_commit': r.GRID_COMMIT,
                  'source': source, 'dataset_manifest': manifest, 'runs': cells}
        r.atomic_json(grid/'ledger.json', ledger)
        audit = {'status': 'verified', 'errors': [], 'ledger_sha256': r.sha(grid/'ledger.json'),
                 'source_verification': {'commit': r.GRID_COMMIT, 'inventory_sha256': r.digest(source)},
                 'counts': {'cells': 18, 'snapshots_checked': 72, 'historical_replays': 9},
                 'training': {'dataset_fingerprint': r.DATA_FINGERPRINT,
                              'manifest_sha256': r.sha(trainpath/'manifest.json'),
                              'payload_sha256': r.sha(trainpath/'data.json')}}
        r.atomic_json(root/'audit.json', audit)
        data = {'manifest': manifest, 'fixture': [1, 2]}
        events = []
        clock = [100.]
        state = SimpleNamespace(root=root, grid=grid, training=trainpath, output=output,
                                manifest=manifest, ledger=ledger, data=data, events=events,
                                source=source, clock=clock)
        def packing(dataset, guard):
            events.append('packing'); guard()
            return {'fixture': [1, 2, 3]}
        def verify(grid):
            self.assertTrue((output/'schedule.json').exists())
            journal = r.read(output/'journal.json')
            self.assertEqual(journal['schedule_sha256'], r.sha(output/'schedule.json'))
            events.append('strict verification')
            return {'status': 'verified_diagnostic', 'verification_errors': [],
                    'ledger_sha256': audit['ledger_sha256'], 'dataset_fingerprint': r.DATA_FINGERPRINT}
        def load(path, config, identity):
            self.assertIn('strict verification', events)
            events.append('load '+r.run_id(config))
            return SimpleNamespace(config=config, epoch=160, step=10560, token=0)
        def measure(model, dataset, schedule, guard):
            guard(); events.append('measure '+r.run_id(model.config))
            return {'rows': [{'config': asdict(model.config), 'game': game, 'target_space': space}
                             for game in ('connect4-4x5', 'reversi6') for space in ('online', 'ema')]}
        def summarize(rows, schedule):
            self.assertEqual(len(rows), 72)
            self.assertEqual(len({(row['config']['variant'], row['config']['hidden'], row['config']['seed'],
                                  row['game'], row['target_space']) for row in rows}), 72)
            return {'status': 'verified_probe', 'verification_errors': [], 'rows': rows}
        replacements = {'ROOT': root, 'AUDIT_PATH': 'audit.json', 'AUDIT_SHA': r.sha(root/'audit.json'),
                        'v23_source': lambda: source, 'source_identity': lambda: source,
                        'verify_bytes': lambda path: (manifest, b'fixture'), 'load_dataset': lambda *args: data,
                        'check_train': lambda obj: None, 'build_schedule': packing, 'summarize_grid': verify,
                        'tensor_hashes': lambda model: {'fixture_tensor': str(model.token)},
                        'measure': measure, 'summarize': summarize,
                        'markdown': lambda report: 'Status: '+report['status']+'\n',
                        'process_peak_rss': lambda: 1_000_000}
        for name, value in replacements.items():
            stack.enter_context(patch.object(r, name, value))
        stack.enter_context(patch.object(r.Model, 'load', side_effect=load))
        stack.enter_context(patch.object(r.time, 'perf_counter', side_effect=lambda: clock[0]))
        stack.enter_context(patch.dict(r.os.environ, {'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'}))
        stack.enter_context(patch('builtins.print'))
        return state

    def test_complete_inventory_packing_saved_before_any_model_and_only_training_loader(self):
        with TemporaryDirectory() as directory, ExitStack() as stack:
            f = self.fixture(stack, directory)
            loader = stack.enter_context(patch.object(r, 'load_dataset', return_value=f.data))
            stack.enter_context(patch('two_player_v22.data.parent_load', side_effect=AssertionError('Parent labels accessed')))
            result = r.run_probe(f.grid, f.training, f.output)
            self.assertEqual(result['status'], 'complete', result['errors'])
            loader.assert_called_once_with(f.training, 'train')
            self.assertEqual(f.events[:2], ['packing', 'strict verification'])
            self.assertEqual(sum(e.startswith('load ') for e in f.events), 18)
            self.assertEqual(sum(e.startswith('measure ') for e in f.events), 18)
            self.assertEqual(len(result['completed_cells']), 18)
            self.assertEqual([result[k] for k in ('optimizer_updates', 'development_predictions',
                             'selection_predictions', 'final_predictions', 'new_search_decisions')], [0]*5)
            self.assertEqual(r.read(f.output/'journal.json'), result)

    def test_prerequisite_byte_tamper_rejected_before_packing_or_model_loading(self):
        with TemporaryDirectory() as directory, ExitStack() as stack:
            f = self.fixture(stack, directory)
            with (f.root/'audit.json').open('a') as stream: stream.write(' ')
            result = r.run_probe(f.grid, f.training, f.output)
            self.assertEqual(result['status'], 'inconclusive')
            self.assertIn('audit bytes changed', result['errors'][0])
            self.assertEqual(f.events, [])
            r.Model.load.assert_not_called()

    def test_strict_prerequisite_failure_prevents_measurements_but_preserves_packing(self):
        with TemporaryDirectory() as directory, ExitStack() as stack:
            f = self.fixture(stack, directory)
            stack.enter_context(patch.object(r, 'summarize_grid', return_value={
                'status': 'inconclusive', 'verification_errors': ['fixture failure']}))
            result = r.run_probe(f.grid, f.training, f.output)
            self.assertEqual(result['status'], 'inconclusive')
            self.assertTrue((f.output/'schedule.json').exists())
            r.Model.load.assert_not_called()
            self.assertEqual(result['completed_cells'], [])

    def test_mutated_model_data_schedule_and_checkpoint_each_fail_entire_attempt(self):
        for kind in ('model', 'data', 'schedule', 'checkpoint'):
            with self.subTest(kind=kind), TemporaryDirectory() as directory, ExitStack() as stack:
                f = self.fixture(stack, directory)
                original = r.measure
                def mutation(model, data, schedule, guard):
                    result = original(model, data, schedule, guard)
                    if kind == 'model': model.token += 1
                    elif kind == 'data': data['fixture'].append(99)
                    elif kind == 'schedule': schedule['fixture'].append(99)
                    else: (f.grid/r.run_id(model.config)/'checkpoint-e160.npz').write_bytes(b'changed fixture')
                    return result
                stack.enter_context(patch.object(r, 'measure', mutation))
                result = r.run_probe(f.grid, f.training, f.output)
                self.assertEqual(result['status'], 'inconclusive')
                self.assertEqual(result['completed_cells'], [])
                self.assertEqual(sum(e.startswith('measure ') for e in f.events), 1)

    def test_time_rss_missing_rss_and_output_caps_fail_and_record_elapsed_work(self):
        for kind in ('time', 'rss', 'missing-rss', 'bytes'):
            with self.subTest(kind=kind), TemporaryDirectory() as directory, ExitStack() as stack:
                f = self.fixture(stack, directory)
                reached = [False]; original = r.measure
                def overrun(*args):
                    result = original(*args); reached[0] = True
                    f.clock[0] += 601. if kind == 'time' else 7.
                    return result
                stack.enter_context(patch.object(r, 'measure', overrun))
                if kind in ('rss', 'missing-rss'):
                    stack.enter_context(patch.object(r, 'process_peak_rss', side_effect=lambda:
                        (r.RSS_BYTES if kind == 'rss' else None) if reached[0] else 1_000_000))
                elif kind == 'bytes':
                    stack.enter_context(patch.object(r, 'output_bytes', side_effect=lambda *args: r.BYTES if reached[0] else 0))
                result = r.run_probe(f.grid, f.training, f.output)
                self.assertEqual(result['status'], 'inconclusive')
                self.assertEqual(result['seconds'], 601. if kind == 'time' else 7.)
                self.assertEqual(result['completed_cells'], [])
                self.assertTrue(result['errors'])

    def test_guard_is_supplied_during_packing_and_blocks_model_access(self):
        with TemporaryDirectory() as directory, ExitStack() as stack:
            f = self.fixture(stack, directory)
            def excessive_packing(data, guard):
                f.clock[0] += 601.; guard()
                raise AssertionError('Overrun should stop packing')
            stack.enter_context(patch.object(r, 'build_schedule', excessive_packing))
            result = r.run_probe(f.grid, f.training, f.output)
            self.assertEqual(result['status'], 'inconclusive')
            self.assertEqual(result['seconds'], 601.)
            r.Model.load.assert_not_called()

    def test_existing_or_nested_output_rejected_without_overwriting_attempt(self):
        with TemporaryDirectory() as directory, ExitStack() as stack:
            f = self.fixture(stack, directory)
            f.output.mkdir(); marker = f.output/'journal.json'; marker.write_text('old attempt')
            with self.assertRaises(FileExistsError): r.run_probe(f.grid, f.training, f.output)
            self.assertEqual(marker.read_text(), 'old attempt')
            with self.assertRaises(ValueError): r.run_probe(f.grid, f.training, f.grid/'probe')
            with self.assertRaises(ValueError): r.run_probe(f.grid, f.training, f.training/'probe')
            r.Model.load.assert_not_called()

    def test_inconclusive_arithmetic_report_cannot_complete_attempt(self):
        with TemporaryDirectory() as directory, ExitStack() as stack:
            f = self.fixture(stack, directory)
            stack.enter_context(patch.object(r, 'summarize', return_value={
                'status': 'inconclusive', 'verification_errors': ['synthetic duplicate/foreign row']}))
            result = r.run_probe(f.grid, f.training, f.output)
            self.assertEqual(result['status'], 'inconclusive')
            self.assertTrue(result['errors'])

    def test_late_output_cap_failure_cannot_leave_unqualified_positive_report(self):
        with TemporaryDirectory() as directory, ExitStack() as stack:
            f = self.fixture(stack, directory)
            real_bytes = r.output_bytes
            def late_bytes(path, exclude_journal=False):
                journal = Path(path)/'journal.json'
                if journal.exists() and r.read(journal).get('status') == 'complete':
                    return r.BYTES
                return real_bytes(path, exclude_journal)
            stack.enter_context(patch.object(r, 'output_bytes', late_bytes))
            result = r.run_probe(f.grid, f.training, f.output)
            self.assertEqual(result['status'], 'inconclusive')
            if (f.output/'report.json').exists():
                report = r.read(f.output/'report.json')
                self.assertTrue(report['status'] != 'verified_probe' or report.get('provisional') is True)

    def test_final_reread_rejects_tampered_saved_schedule_or_earlier_measurement(self):
        for kind in ('schedule', 'measurement'):
            with self.subTest(kind=kind), TemporaryDirectory() as directory, ExitStack() as stack:
                f = self.fixture(stack, directory)
                original = r.summarize
                def alter_saved_output(rows, schedule):
                    report = original(rows, schedule)
                    name = 'schedule.json' if kind == 'schedule' else r.run_id(r.configurations()[0])+'.json'
                    path = f.output/name
                    with path.open('a', encoding='utf-8') as stream:
                        stream.write(' ')  # Valid JSON, different immutable file bytes.
                    return report
                stack.enter_context(patch.object(r, 'summarize', alter_saved_output))
                result = r.run_probe(f.grid, f.training, f.output)
                self.assertEqual(len(result['completed_cells']), 18)
                self.assertEqual(result['status'], 'inconclusive')
                self.assertIn('Saved '+kind+' changed', result['errors'][0])
                self.assertEqual(r.read(f.output/'report.json')['status'], 'inconclusive')


if __name__ == '__main__':
    unittest.main()
