"""MARS-JEPA hardening regressions; every artifact lives in TemporaryDirectory."""
import copy
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import random
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch
import numpy as np
from main import pgnparser, vitriengine, text_thanh_move
from fen_dataset_tool import FenDatasetBuilder
from adversarial_jepa import iter_dataset_games, sample_from_dataset_position, AdversarialJEPA, encode_action, encode_snapshot, snapshot_from_engine
from model_registry import training_model_specs, create_model, model_manifest, spec_by_id
from research_dataset import resolve_dataset, checkpoint_compatibility, audit_dataset, publish_audit, verify_plan, position_keys
from research_diagnostics import finite_difference_check, latent_diagnostics, seed_stability
from confirmatory_protocol import protocol_manifest, gate, confirmatory_result, paired_interval, holm_adjust
from arena_store import ArenaHistory
from train_caissa_v7 import train
from runtime_safety import atomic_json, checkpoint_commit, restore_committed
from test_pipeline_recovery import args
import test_model_arena as fixtures
from test_model_arena import GM_PGN


def disjoint_fixture(root):
    from arena_protocol import OPENINGS
    parser = pgnparser()
    texts = []
    for i, (_, line) in enumerate(OPENINGS[6:26]):
        engine = vitriengine(parser.tao_snapshot_ban_dau(), .01)
        for uci in line.split():
            engine.thuc_hien_nuoc_di(text_thanh_move(uci, engine.turn))
        fen = parser.snapshot_thanh_fen(snapshot_from_engine(engine))
        moves = []
        for _ in range(4):
            legal = engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)
            if not legal:
                break
            move = random.Random(i+len(moves)).choice(legal)
            moves.append(parser.tao_san(engine, move, legal))
            engine.thuc_hien_nuoc_di(move)
        texts.append(f'[Event "Fixture {i:02d}"]\n[Date "2026.01.{i+1:02d}"]\n[WhiteTitle "GM"]\n[Result "1-0"]\n[SetUp "1"]\n[FEN "{fen}"]\n\n'+' '.join(moves)+' 1-0\n')
    source = root / 'fixture.pgn'
    source.write_text('\n'.join(texts), encoding='utf-8')
    dataset = root / 'dataset'
    builder = FenDatasetBuilder(dataset, 1024*1024, 32768, {'GM'}, False)
    builder.ingest_path(source, {'name': 'synthetic temporary fixtures', 'license': 'CC0 synthetic fixture'})
    builder.close('COMPLETE')
    return dataset


class HardeningTests(unittest.TestCase):
    def test_release_selftest_uses_temporary_fixtures(self):
        from release_smoke import run
        import contextlib, io
        with tempfile.TemporaryDirectory(prefix="mars-release-check-") as folder:
            output = Path(folder) / "receipt.json"
            with contextlib.redirect_stdout(io.StringIO()):
                code = run(output)
            receipt = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(code, 0, receipt)
            self.assertEqual(receipt["status"], "PASSED")
            self.assertEqual(sum(c.startswith("train/resume ") for c in receipt["checks"]), 7)

    def test_missing_data_stale_location_and_missing_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for path in (root/'missing', root/'empty'):
                if path.name == 'empty': path.mkdir()
                atomic_json(root/'chess_data/dataset_location.json', {'path': str(path)})
                with self.assertRaises(FileNotFoundError): resolve_dataset(root)
            atomic_json(root/'chess_data/dataset_location.json', {'path': 'relative'})
            with self.assertRaises(ValueError): resolve_dataset(root)
            atomic_json(root/'chess_data/dataset_location.json', {'wrong': 1})
            with self.assertRaises(KeyError): resolve_dataset(root)

    @unittest.skipUnless(os.name == 'nt', 'Windows junction regression')
    def test_broken_junction_cannot_fall_back_to_cache(self):
        import _winapi
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root/'target'; target.mkdir()
            junction = root/'junction'
            _winapi.CreateJunction(str(target), str(junction))
            target.rmdir()
            try:
                with self.assertRaises(FileNotFoundError): resolve_dataset(root, junction)
            finally:
                os.rmdir(junction)

    def test_checkpoint_missing_fingerprint_is_unverified(self):
        with tempfile.TemporaryDirectory() as folder:
            model = AdversarialJEPA(Path(folder)/'a.npz', latent_size=4)
            self.assertFalse(checkpoint_compatibility(model, None)['compatible'])
            self.assertFalse(checkpoint_compatibility(model, 'x')['compatible'])
            model.dataset_fingerprint = 'x'
            self.assertTrue(checkpoint_compatibility(model, 'x')['compatible'])
            self.assertFalse(checkpoint_compatibility(model, 'y')['compatible'])

    def test_all_variants_registry_serialization_and_manual_gradients(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); dataset = fixtures.ModelArenaTests().build_dataset(root)
            samples = [sample_from_dataset_position(p, np.random.default_rng(7)) for p in next(iter_dataset_games(dataset))['positions'][:5]]
            for spec in training_model_specs(root):
                with self.subTest(model=spec['id']):
                    model = create_model(spec, latent_size=4)
                    manifest = model_manifest(spec, model)
                    self.assertGreater(manifest['parameters'], 0)
                    self.assertEqual(manifest['research_name'], 'MARS-JEPA Chess')
                    before = copy.deepcopy(model.__dict__)
                    checks = finite_difference_check(model, samples)
                    self.assertTrue(all(c['passed'] for c in checks), [c for c in checks if not c['passed']])
                    self.assertEqual(model.trained_steps, before['trained_steps'])
                    model.train_batch(samples)
                    model.save()
                    loaded = create_model(spec, create_if_missing=False)
                    self.assertEqual(model_manifest(spec, loaded), model_manifest(spec, model))
                    self.assertAlmostEqual(model.danh_gia_snapshot(samples[0]['state']), loaded.danh_gia_snapshot(samples[0]['state']))
            self.assertEqual(spec_by_id(root, 'h1-h2')['variant'], 'h1-h2')

    def test_all_variants_fresh_collision_resume_stop_rollback_and_recovery(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); dataset = fixtures.ModelArenaTests().build_dataset(root)
            for spec in training_model_specs(root):
                with self.subTest(model=spec['id']):
                    arguments = args(dataset, spec['path'])
                    arguments.architecture, arguments.model_variant = spec['architecture'], spec['variant']
                    train(arguments)
                    first = json.loads(spec['path'].with_suffix('.training.json').read_text())
                    with self.assertRaises(FileExistsError): train(arguments)
                    failure = json.loads(spec['path'].with_suffix('.training.json').read_text())
                    for field in ('phase', 'pid', 'run_id', 'dataset_fingerprint', 'model_configuration', 'traceback', 'path_diagnostics'):
                        self.assertIn(field, failure)
                    arguments.resume = True
                    stop = threading.Event(); stop.set(); arguments.stop_event = stop
                    with self.assertRaises(KeyboardInterrupt): train(arguments)
                    stopped = json.loads(spec['path'].with_suffix('.training.json').read_text())
                    self.assertEqual(stopped['trained_steps'], first['trained_steps'])
                    stop.clear()
                    arguments.max_train_batches = 3
                    def interrupt_after_update(report):
                        if report.get("phase") == "train":
                            stop.set()
                    with self.assertRaises(KeyboardInterrupt):
                        train(arguments, interrupt_after_update)
                    rolled_back = json.loads(spec['path'].with_suffix('.training.json').read_text())
                    self.assertEqual(rolled_back['trained_steps'], first['trained_steps'])
                    self.assertGreater(rolled_back['uncommitted_steps_discarded'], 0)
                    stop.clear()
                    arguments.max_train_batches = 1
                    train(arguments)
                    resumed = json.loads(spec['path'].with_suffix('.training.json').read_text())
                    self.assertGreater(resumed['trained_steps'], first['trained_steps'])
                    model = create_model(spec, create_if_missing=False)
                    expected = model.danh_gia_snapshot(pgnparser().tao_snapshot_ban_dau())
                    with patch('runtime_safety.atomic_json', side_effect=OSError('partial pointer write')):
                        with self.assertRaises(OSError): checkpoint_commit(model, {'completed_epochs': 999})
                    restore_committed(spec['path'])
                    self.assertAlmostEqual(create_model(spec, create_if_missing=False).danh_gia_snapshot(pgnparser().tao_snapshot_ban_dau()), expected)

    def test_explicit_fresh_archive_preserves_old_checkpoint(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); dataset=fixtures.ModelArenaTests().build_dataset(root)
            arguments=args(dataset,root/'model.npz')
            train(arguments)
            old=(root/'model.npz').read_bytes()
            arguments.archive_existing=True
            train(arguments)
            report=json.loads((root/'model.training.json').read_text())
            archive=Path(report['archived_checkpoint'])
            self.assertEqual((archive/'model.npz').read_bytes(),old)
            self.assertTrue((archive/'model.generations/latest.json').exists())

    def test_zero_epoch_and_production_without_audit_fail_before_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); dataset = fixtures.ModelArenaTests().build_dataset(root)
            arguments = args(dataset, root/'new.npz'); arguments.epochs=0
            with self.assertRaisesRegex(ValueError, 'positive'): train(arguments)
            arguments.epochs=1; arguments.fixture_only=False
            with patch('train_caissa_v7.SampleCache.prepare', side_effect=AssertionError('must not cache')):
                with self.assertRaisesRegex(ValueError, 'version-2'): train(arguments)
            self.assertFalse((root/'new.npz').exists())

    def test_complete_fen_semantics_and_undo(self):
        with tempfile.TemporaryDirectory() as folder:
            dataset = fixtures.ModelArenaTests().build_dataset(Path(folder))
            position = next(iter_dataset_games(dataset))['positions'][1]
            self.assertEqual(position['next_fen'].split()[5], '2')
            self.assertIsNotNone(sample_from_dataset_position(position, np.random.default_rng(0)))
            for field, replacement in ((1,'b'),(2,'-'),(3,'-'),(4,'17'),(5,'98')):
                corrupted=copy.deepcopy(position); parts=corrupted['next_fen'].split(); parts[field]=replacement; corrupted['next_fen']=' '.join(parts)
                self.assertIsNone(sample_from_dataset_position(corrupted,np.random.default_rng(0)), field)
        parser=pgnparser(); state=parser.fen_thanh_snapshot('7k/8/8/8/8/8/8/K7 b - - 12 37')
        engine=vitriengine(state,.01); move=engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)[0]
        undo=engine.thuc_hien_nuoc_di(move); self.assertEqual(engine.fullmove_number,38)
        engine.hoan_tac_nuoc_di(undo); self.assertEqual(parser.snapshot_thanh_fen(snapshot_from_engine(engine)), '7k/8/8/8/8/8/8/K7 b - - 12 37')
        for fen in ('8/8/8/8/8/8/8/8 x - - 0 1','8/8/8/8/8/8/8/8 w - - -1 1','8/8/8/8/8/8/8/8 w - - 0 0'):
            with self.assertRaises(ValueError): parser.fen_thanh_snapshot(fen)

    def test_parser_castling_promotion_en_passant_terminal_and_skip_ledger(self):
        cases=[('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1','O-O O-O-O'),
               ('7k/P7/8/8/8/8/8/7K w - - 0 1','a8=Q+'),
               ('7k/8/8/3pP3/8/8/8/7K w - d6 0 1','exd6')]
        parser=pgnparser()
        for fen, moves in cases:
            parsed=parser.parse_game(f'[SetUp "1"]\n[FEN "{fen}"]\n[Result "1-0"]\n\n{moves} 1-0')
            self.assertTrue(parsed['records'])
        for fen, check in [('7k/6Q1/6K1/8/8/8/8/8 b - - 0 1', True),('7k/5Q2/6K1/8/8/8/8/8 b - - 0 1',False)]:
            engine=vitriengine(parser.fen_thanh_snapshot(fen),.01)
            self.assertFalse(engine.lay_tat_ca_nuoc_di_hop_le(engine.turn))
            self.assertEqual(engine.is_king_in_check(engine.turn),check)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); source=root/'invalid.pgn'
            source.write_text(GM_PGN.replace('e4 e5','N@f3 e5')+'\n'+GM_PGN.replace('e4 e5','Xx9 e5'))
            builder=FenDatasetBuilder(root/'data',100000,32768,{'GM'},False)
            stats=builder.ingest_path(source,{'name':'fixture'}); builder.close('COMPLETE')
            self.assertEqual(stats['skipped'],2)
            self.assertEqual(stats['skip_reasons']['unsupported_move'],1)
            self.assertEqual(stats['skip_reasons']['malformed_or_illegal_move'],1)
            self.assertEqual(len((root/'data/parser_quarantine.jsonl').read_text().splitlines()),2)

    def test_audit_disjoint_splits_provenance_and_invalidation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); dataset=disjoint_fixture(root)
            plan_path=root/'audit.json'; plan=publish_audit(dataset,plan_path)
            self.assertEqual(plan['status'],'PASSED',plan['errors'])
            self.assertEqual(plan,verify_plan(dataset,plan_path))
            split_keys={s:set() for s in ('train','validation','test')}
            for game in iter_dataset_games(dataset):
                for i in plan['included_position_indices'].get(game['game_hash'],[]):
                    split_keys[plan['assignments'][game['game_hash']]].update(position_keys(game['positions'][i]))
            for a,b in (('train','validation'),('train','test'),('validation','test')):
                self.assertFalse(split_keys[a]&split_keys[b])
            corrupted=copy.deepcopy(plan); corrupted['included_position_indices']={}
            atomic_json(plan_path,corrupted)
            with self.assertRaises(ValueError): verify_plan(dataset,plan_path)

    def test_response_expectation_not_minimum_and_horizon_masks(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); dataset=fixtures.ModelArenaTests().build_dataset(root)
            sample=sample_from_dataset_position(next(iter_dataset_games(dataset))['positions'][0],np.random.default_rng(0))
            model=AdversarialJEPA(root/'a.npz',latent_size=4)
            model.policy_action_w.fill(0)
            def values(latent): return np.linspace(-.8,.8,len(latent))[:,None]
            with patch.object(model,'value',side_effect=values):
                scores,_,_=model.score_legal_moves(sample['state'],[sample['own_action']])
            self.assertAlmostEqual(scores[0],0,places=5)
            model_h1=AdversarialJEPA(root/'h1.npz',latent_size=4,variant='h1')
            with patch.object(model_h1,'value',return_value=np.array([[.7]])):
                scores,_,_=model_h1.score_legal_moves(sample['state'],[sample['own_action']])
            self.assertAlmostEqual(scores[0],-.7)
            masked=copy.deepcopy(sample); masked['future2']=masked['future4']=None
            metrics=model.train_batch([masked])
            self.assertEqual(metrics['h2_loss'],0); self.assertEqual(metrics['h4_loss'],0)

    def test_sqlite_partial_iterator_closes_and_concurrent_import_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); store=ArenaHistory(root/'history.sqlite')
            source=root/'history.jsonl'; source.write_text('\n'.join(json.dumps({'series_id':str(i)}) for i in range(200))+'\n')
            store.import_jsonl(source); store.import_jsonl(source)
            self.assertEqual(len(store),200)
            iterator=iter(store); next(iterator)
            with sqlite3.connect(store.path,timeout=.1) as db:
                db.execute('BEGIN EXCLUSIVE'); db.commit()
            db.close()
            with ThreadPoolExecutor(2) as pool:
                futures=[pool.submit(store.append,{'series_id':'new'}),pool.submit(lambda:len(list(store)))]
                for future in futures: future.result()
            self.assertEqual(len(store),201)
            iterator.close()
            moved=root/'moved.sqlite'; store.path.rename(moved); moved.unlink()

    def test_common_search_enforces_nodes_and_value_perspective(self):
        from research_search import search_move, ALGORITHM
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            config = {"algorithm": ALGORITHM, "nodes": 8, "move_seconds": 1.0, "overrun_tolerance_seconds": .05}
            snapshot = pgnparser().tao_snapshot_ban_dau()
            legal = vitriengine(snapshot, .01).lay_tat_ca_nuoc_di_hop_le("white")
            for spec in training_model_specs(root):
                model = create_model(spec, latent_size=4)
                move, record = search_move(model, snapshot, config)
                self.assertIn(move, legal)
                self.assertLessEqual(record['nodes'], 8)
            model = create_model(training_model_specs(root)[0], latent_size=4)
            snapshot = pgnparser().fen_thanh_snapshot('7k/5Q2/6K1/8/8/8/8/8 w - - 0 1')
            config.update(nodes=100, depth_cap=1)
            with patch.object(model, 'danh_gia_snapshot', return_value=0.0):
                move, record = search_move(model, snapshot, config)
            engine = vitriengine(snapshot, .01); engine.thuc_hien_nuoc_di(move)
            self.assertFalse(engine.lay_tat_ca_nuoc_di_hop_le(engine.turn))
            self.assertTrue(engine.is_king_in_check(engine.turn))

    def test_paired_adapter_records_budgeted_censored_fixture_games(self):
        from research_search import play_pair, ALGORITHM
        from dataset_integrity import sha256_file
        from unittest.mock import MagicMock
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); dataset=fixtures.ModelArenaTests().build_dataset(root)
            sample=sample_from_dataset_position(next(iter_dataset_games(dataset))['positions'][0],np.random.default_rng(0))
            protocol=protocol_manifest()
            protocol['openings']=protocol['openings'][:1]
            protocol['search'].update(nodes=8,move_seconds=1.,max_plies=1)
            protocol['dataset_fingerprint']='temporary fixture'
            protocol['referee']={'sha256':'fixture stub'}
            for spec in training_model_specs(root)[:2]:
                model=create_model(spec,latent_size=4); model.dataset_fingerprint=protocol['dataset_fingerprint']; model.train_batch([sample]); model.save()
                protocol['models'].append({'registry_id':spec['id'],'seed_checkpoints':{str(model.seed):{'path':str(spec['path']),'sha256':sha256_file(spec['path'])}}})
            context=MagicMock(); context.__enter__.return_value.evaluate.return_value={'source':'fixture stub'}
            with patch('confirmatory_protocol.pinned_referee',return_value=context):
                records=play_pair(protocol,0,20260903)
            self.assertEqual({r['candidate_color'] for r in records},{'white','black'})
            self.assertTrue(all(r['result']=='*' and r['reason']=='MAX_PLIES' for r in records))
            self.assertTrue(all(r['move_records'][0]['nodes']<=8 for r in records))
            self.assertFalse(confirmatory_result(protocol,records)['ranking_ready'])

    def test_pinned_referee_requires_live_hash_version_and_options(self):
        from confirmatory_protocol import pinned_referee
        from dataset_integrity import sha256_file
        from unittest.mock import MagicMock
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "referee.bin"; path.write_bytes(b"test fixture only")
            config = {"path": str(path), "sha256": sha256_file(path), "version": "Fixture UCI 1",
                      "options": {"Threads": 1}, "milliseconds": 10, "independent": True}
            engine = MagicMock(); engine.name = config['version']; engine.digest = config['sha256']
            with patch('arena_research.UCIReferee', return_value=engine) as constructor:
                with pinned_referee(config) as actual: self.assertIs(actual, engine)
                constructor.assert_called_once_with(path, milliseconds=10, options={'Threads':1})
                engine.close.assert_called_once()
                engine.name = "different version"
                with self.assertRaisesRegex(ValueError, 'version/hash'):
                    with pinned_referee(config): pass
            path.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, 'checksum'):
                with pinned_referee(config): pass

    def test_confirmatory_referee_gates_pairs_censoring_and_statistics(self):
        protocol=protocol_manifest(final=True)
        self.assertEqual(len(protocol['openings']),100)
        self.assertFalse(gate(protocol)['protocol_ready'])
        self.assertFalse(confirmatory_result(protocol,[])['ranking_ready'])
        records=[{'opening_id':i,'model_seed':seed,'candidate_color':color,'result':'1-0' if color=='white' else '0-1'} for i in range(3) for seed in (1,2,3) for color in ('white','black')]
        stats=paired_interval(records); self.assertEqual(stats['score'],1); self.assertEqual(stats['complete_pairs'],9)
        records[0]['reason']='TIMEOUT'; self.assertEqual(paired_interval(records)['complete_pairs'],8)
        self.assertEqual(holm_adjust([.01,.04,.03]),[.03,.06,.06])

    def test_latent_collapse_and_seed_stability_diagnostics(self):
        self.assertEqual(latent_diagnostics(np.ones((4,3)))['effective_rank'],0)
        self.assertGreater(latent_diagnostics(np.eye(4))['effective_rank'],2)
        with self.assertRaises(ValueError): seed_stability([{'seed':1,'metric':1}])
        self.assertEqual(seed_stability([{'seed':i,'metric':float(i)} for i in (1,2,3)])['mean'],2)

if __name__=='__main__': unittest.main()
