"""Regression evidence for the research roster, trainer and arena protocol."""
import copy
import json
import os
import tempfile
import threading
import time
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QFontDatabase, QFont
from PySide6.QtTest import QTest

from adversarial_jepa import AdversarialJEPA, snapshot_from_fen, sample_from_dataset_position, iter_dataset_games, dataset_manifest_fingerprint
from lejepa import LeJEPA
from policy_value_baseline import DirectPolicyValueBaseline
from arena_research import parse_uci_info, evaluation_display, completed_records, matchup_statistics, Referee, UCIReferee
from training_runtime import TrainingETA, MetricMean, SampleCache
from main import boardwidget, monitor_window, modelmatchworker, vitriengine, text_thanh_move
from model_registry import training_model_specs
import test_model_arena as arena_fixture


class ResearchUpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        for font in ("consola.ttf", "consolab.ttf", "segoeui.ttf"):
            path = Path(os.environ.get("WINDIR", "C:/Windows"))/"Fonts"/font
            if path.exists():
                QFontDatabase.addApplicationFont(str(path))
        cls.app.setFont(QFont("Consolas", 9))

    def test_eta_provisional_calibrated_and_complete(self):
        eta = TrainingETA({"train": 4, "validation": 2}, 2)
        self.assertIsNone(eta.fields()["eta_seconds"])
        for _ in range(3):
            eta.observe("train", 2)
        self.assertIn("PROVISIONAL", eta.fields()["eta_status"])
        for _ in range(2):
            eta.observe("validation", 1)
        self.assertEqual(eta.fields()["eta_seconds"], 12)
        self.assertEqual(eta.fields()["overall_total"], 12)
        self.assertIn("PILOT", eta.fields()["eta_status"])
        for _ in range(5):
            eta.observe("train", 2)
        for _ in range(2):
            eta.observe("validation", 1)
        self.assertEqual(eta.fields()["progress_percent"], 100)
        self.assertEqual(eta.fields()["eta_seconds"], 0)

    def test_weighted_metrics_and_nonfinite(self):
        metric = MetricMean()
        metric.add({"loss": 2}, 3)
        metric.add({"loss": 6}, 1)
        self.assertEqual(metric.result()["loss"], 3)
        with self.assertRaises(FloatingPointError):
            metric.add({"loss": float("nan")}, 1)

    def test_uci_white_pov_mate_bounds_and_wdl(self):
        info = parse_uci_info("info depth 18 nodes 200 nps 400 score cp 180 lowerbound wdl 600 300 100 pv e7e5", "black")
        self.assertEqual(info["cp_white"], -180)
        self.assertEqual(info["wdl_white"], [100, 300, 600])
        self.assertEqual(info["bound"], "upperbound")
        self.assertEqual(evaluation_display(info)[0], .25)
        self.assertEqual(parse_uci_info("info score mate -3", "black")["mate_white"], 3)
        self.assertNotIn("%", evaluation_display({"cp_white": 100})[1])

    def test_uci_timeout_and_cancel_are_bounded(self):
        import queue
        referee = UCIReferee.__new__(UCIReferee)
        referee.lines = queue.Queue()
        started = time.monotonic()
        with self.assertRaises(TimeoutError):
            referee.until("readyok", .02)
        self.assertLess(time.monotonic()-started, .5)
        stop = threading.Event()
        stop.set()
        with self.assertRaises(InterruptedError):
            referee.until("readyok", 4, stop)

    def test_uci_subprocess_handshake_analysis_and_shutdown(self):
        script = Path(__file__).parent/"tests/fixtures/uci_referee_stub.py"
        referee = UCIReferee(sys.executable, command=[sys.executable,"-B",str(script)])
        try:
            self.assertEqual(referee.name, "Test referee")
            score = referee.evaluate(["e2e4"], "black")
            self.assertEqual(score["cp_white"], -25)
            self.assertEqual(score["wdl_white"], [100,700,200])
        finally:
            referee.close()
        self.assertIsNotNone(referee.process.poll())

    def test_action_ranking_writes_checkpoint_bound_metrics(self):
        from evaluate_action_ranking import evaluate
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dataset = arena_fixture.ModelArenaTests().build_dataset(root)
            path = root/"pv.npz"
            DirectPolicyValueBaseline(path, latent_size=8).save()
            result = evaluate(dataset,path,"policy-value","train",1,2,fixture_only=True)
            self.assertEqual(result["positions"],2)
            self.assertTrue(path.with_suffix(".evaluation.json").exists())
            self.assertGreater(result["mean_reciprocal_rank"],0)

    def test_nnue_evaluator_side_perspective(self):
        class ConstantSideEvaluator:
            def evaluate_engine_score(self, engine):
                return 125
        for turn, expected in (("w",125),("b",-125)):
            snapshot = snapshot_from_fen(f"4k3/8/8/8/8/8/4P3/4K3 {turn} - - 0 1")
            engine = vitriengine(snapshot, evaluation_model=ConstantSideEvaluator())
            self.assertEqual(engine.tinh_evaluation(), expected)
            self.assertEqual(engine.tinh_evaluation_theo_luot(), 125)

    def test_jepa_mate_and_h1_never_uses_untrained_h2(self):
        snapshot = snapshot_from_fen("rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq g3 0 2")
        mate = text_thanh_move("d8h4", "black")
        with tempfile.TemporaryDirectory() as folder:
            for variant in ("h1", "full"):
                model = AdversarialJEPA(Path(folder)/f"{variant}.npz", latent_size=8, variant=variant)
                self.assertEqual(model.score_legal_moves(snapshot, [mate])[0], [1.0])
            model = AdversarialJEPA(Path(folder)/"h1.npz", latent_size=8, variant="h1")
            original = model._predict
            def checked(latent, actions, horizon):
                self.assertEqual(horizon, 1)
                return original(latent, actions, horizon)
            model._predict = checked
            legal = vitriengine(snapshot).lay_tat_ca_nuoc_di_hop_le("black")
            model.score_legal_moves(snapshot, legal[:3])

    def test_cache_reuse_shuffle_and_invalid_targets(self):
        with tempfile.TemporaryDirectory() as folder:
            dataset = arena_fixture.ModelArenaTests().build_dataset(Path(folder))
            cache = SampleCache(dataset, dataset_manifest_fingerprint(dataset), 1).prepare()
            first = list(cache.batches("train", 2, 7))
            self.assertTrue(first)
            with patch("adversarial_jepa.iter_dataset_games", side_effect=AssertionError("cache unexpectedly rebuilt")):
                SampleCache(dataset, dataset_manifest_fingerprint(dataset), 1).prepare()
            self.assertEqual(first, list(cache.batches("train", 2, 7)))
            position = copy.deepcopy(next(iter_dataset_games(dataset))["positions"][0])
            position["next_fen"] = position["fen"]
            self.assertIsNone(sample_from_dataset_position(position, np.random.default_rng(0)))

    def test_cache_parallel_shards_resume_format(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dataset = arena_fixture.ModelArenaTests().build_dataset(root)
            manifest_path = dataset / "dataset_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            first = manifest["shards"][0]
            source = dataset / first["path"]
            duplicate = dataset / "shards" / "parallel_copy.jsonl"
            duplicate.write_bytes(source.read_bytes())
            manifest["shards"].append({
                "path": "shards/parallel_copy.jsonl",
                "bytes": duplicate.stat().st_size,
                "sha256": first.get("sha256", "parallel-copy"),
            })
            manifest["positions"] = int(manifest.get("positions", 0)) * 2
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            fingerprint = dataset_manifest_fingerprint(dataset)
            cache = SampleCache(dataset, fingerprint, 1, workers=2).prepare()
            self.assertGreater(cache.counts["train"] + cache.counts["validation"], 0)
            self.assertEqual(cache.path.name.startswith(f"prepared-v{SampleCache.VERSION}-"), True)
            self.assertTrue((cache.path / "manifest.json").exists())
            resumed = SampleCache(dataset, fingerprint, 1, workers=2).prepare()
            self.assertEqual(cache.counts, resumed.counts)
    def test_losses_match_gradient_weights_and_single_legal_mask(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dataset = arena_fixture.ModelArenaTests().build_dataset(root)
            sample = sample_from_dataset_position(next(iter_dataset_games(dataset))["positions"][0], np.random.default_rng(0))
            sample["negative_action"] = sample["own_action"]
            for cls in (AdversarialJEPA, DirectPolicyValueBaseline, LeJEPA):
                model = cls(root/f"{cls.__name__}.npz", latent_size=8)
                metrics = model.evaluate_batch([sample])
                self.assertEqual(metrics["ranking_loss"], 0)
                self.assertEqual(metrics["ranking_accuracy"], 0)
                if cls is not LeJEPA:
                    expected = metrics["value_loss"]+.05*metrics.get("variance_loss", .05)
                    expected += metrics.get("h1_loss",0)+.75*metrics.get("h2_loss",0)+.5*metrics.get("h4_loss",0)
                    self.assertAlmostEqual(metrics["loss"], expected, places=6)
                else:
                    before = model.sigreg_slices.copy()
                    model.train_batch([sample])
                    self.assertFalse(np.array_equal(before, model.sigreg_slices))
                    self.assertFalse(hasattr(model,"target_w"))

    def test_completed_stats_exclude_replays_cancellations_and_censored_games(self):
        a = {"series_id":"s", "match_seed":7,"white_model_id":"a","black_model_id":"b","result":"1-0","paired_colors":True}
        b = {**a,"white_model_id":"b","black_model_id":"a","result":"1/2-1/2"}
        records = [a,a,b,{**a,"match_seed":8,"cancelled":True},{**a,"match_seed":9,"reason":"MAX_PLIES"}]
        self.assertEqual(len(completed_records(records)),2)
        stats = matchup_statistics(records,"a","b")
        self.assertEqual(stats["score"],.75)
        self.assertEqual(stats["pairs"],1)
        self.assertEqual(stats["score_ci95"],[0,1])

    def test_arena_history_san_pgn_fullmove_referee_and_color_swap(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            model = AdversarialJEPA(root/"chess_data/caissa_a_jepa_h1.npz", latent_size=8, variant="h1")
            model.save()
            results=[]
            for first,second in (("alpha-beta","a-jepa-h1"),("a-jepa-h1","alpha-beta")):
                worker = modelmatchworker(root,root/"book.sqlite",first,second,threading.Event(),move_time=.05,max_plies=2,forced_match_seed=9)
                worker.ket_qua.connect(results.append)
                worker.chay()
            self.assertEqual(results[0]["white_model_id"],results[1]["black_model_id"])
            for result in results:
                self.assertNotIn("error",result)
                self.assertEqual(result["reason"],"MAX_PLIES")
                self.assertEqual(result["result"],"*")
                self.assertEqual(len(result["san_moves"]),2)
                self.assertTrue(result["move_records"][-1]["fen_after"].endswith(" 2"))
                self.assertIn("evaluation",result["move_records"][0])
            self.assertTrue((root/"chess_data/arena_results.pgn").exists())

    def test_monitor_switches_and_all_model_plots_render(self):
        with tempfile.TemporaryDirectory() as folder:
            board=boardwidget(project_dir=Path(folder))
            project=Path(__file__).resolve().parent
            for piece,filename in board.piece_to_file.items():
                board.piece_renderers[piece]=QSvgRenderer(str(project/"assets/chess_pieces"/filename))
            window=monitor_window(board)
            window.resize(1500,1000)
            monitor=window.monitor_widget
            for index,spec in enumerate(training_model_specs(Path(folder))):
                for step in range(20):
                    monitor.nhan_train({"model_id":spec["id"],"model_label":spec["label"],"trained_steps":step,"overall_processed":step,"overall_total":40,"progress_percent":step*2.5,"metrics":{"loss":1/(step+1)+index*.1},"phase":"validation" if step%5==0 else "train","eta_seconds":123,"estimated_finish_timestamp":time.time()+123,"eta_status":"MEASURED ESTIMATE","rows_per_second":234})
            window.show()
            self.app.processEvents()
            render_dir=os.environ.get("CAISSA_TEST_RENDER_DIR")
            if render_dir:
                Path(render_dir).mkdir(parents=True,exist_ok=True)
                monitor.grab().save(str(Path(render_dir)/"training-monitor.png"))
            for _ in range(3):
                window.set_mode("model-v-model")
                self.app.processEvents()
                window.set_mode("monitor")
                self.app.processEvents()
                self.assertIs(window.centralWidget(),monitor)
            window.set_mode("model-v-model")
            arena=window.modelmatch_widget
            arena.white_model_id="a-jepa-v7"
            arena.black_model_id="lejepa-sigreg"
            arena.specs_by_id.update({s["id"]:s for s in training_model_specs(Path(folder))})
            arena.evaluation={"source":"Classical referee (uncalibrated)","cp_white":45,"depth":4,"ply":0}
            self.app.processEvents()
            if render_dir:
                arena.grab().save(str(Path(render_dir)/"arena-monitor.png"))
            self.assertFalse(arena.grab().isNull())
            window.close()
            board.close()

    def test_live_series_advances_pairs_and_stops_without_losing_history(self):
        from main import modelmatchwidget
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            model = AdversarialJEPA(root/'chess_data/caissa_a_jepa_h1.npz', latent_size=8, variant='h1')
            arena_fixture.verified_arena_fixture(root, [model])
            board = boardwidget(project_dir=root)
            arena = modelmatchwidget(board)
            original = modelmatchworker
            def short_worker(*args, **kwargs):
                kwargs.update(max_plies=2, move_time=.05)
                return original(*args, **kwargs)
            try:
                with patch('main.modelmatchworker', side_effect=short_worker):
                    arena.start_series()
                    deadline = time.monotonic()+8
                    while len(arena.arena_history)<4 and time.monotonic()<deadline:
                        self.app.processEvents()
                        time.sleep(.01)
                    arena.stop_series()
                    while arena.match_running and time.monotonic()<deadline:
                        self.app.processEvents()
                        time.sleep(.01)
                self.assertGreaterEqual(len(arena.arena_history),4, (arena.status_label.text(), arena.arena_history, getattr(arena,'series_signature',None)))
                self.assertFalse(arena.match_running)
                self.assertFalse(board.arena_series_active)
                for index in (0,2):
                    a,b=arena.arena_history[index:index+2]
                    self.assertEqual(a['match_seed'],b['match_seed'])
                    self.assertEqual(a['white_model_id'],b['black_model_id'])
                self.assertTrue(arena.arena_checkpoint_path.exists())
            finally:
                arena.close()
                board.close()


if __name__=="__main__":
    unittest.main(verbosity=2)
