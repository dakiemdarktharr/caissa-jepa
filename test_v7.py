"""Offline integration tests for the CAISSA-JEPA v7 data pipeline."""

import json
import tempfile
import threading
import unittest
from argparse import Namespace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from fen_dataset_tool import (
    FenDatasetBuilder,
    ResilientDownloader,
    atomic_json_write,
    command_verify,
    read_json_with_retry,
)
from adversarial_jepa import (
    AdversarialJEPA,
    iter_dataset_games,
    sample_from_dataset_position,
    snapshot_from_fen,
)
from train_caissa_v7 import train
from policy_value_baseline import DirectPolicyValueBaseline
from evaluate_action_ranking import evaluate
from main import engineworker, vitriengine
import numpy as np


GM_PGN = '''[Event "GM sample"]
[Site "local"]
[Date "2026.01.01"]
[Round "1"]
[White "Alpha"]
[Black "Beta"]
[WhiteTitle "GM"]
[BlackTitle "IM"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0

[Event "Not titled"]
[Site "local"]
[White "Gamma"]
[Black "Delta"]
[Result "1-0"]

1. d4 d5 1-0
'''


class _RangeHandler(BaseHTTPRequestHandler):
    payload = b"CAISSA-JEPA resilient range download test payload"

    def do_GET(self):
        start = 0
        range_header = self.headers.get("Range")
        if range_header:
            start = int(range_header.removeprefix("bytes=").removesuffix("-"))
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{len(self.payload) - 1}/{len(self.payload)}")
        else:
            self.send_response(200)
        body = self.payload[start:]
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


class V7DataPipelineTests(unittest.TestCase):
    def test_atomic_manifest_remains_readable_during_status_polling(self):
        """Regression for Windows sharing violations during crawler polling."""
        with tempfile.TemporaryDirectory() as temporary:
            manifest = Path(temporary) / "dataset_manifest.json"
            atomic_json_write(manifest, {"version": 0})
            stop = threading.Event()
            errors: list[Exception] = []

            def reader() -> None:
                while not stop.is_set():
                    try:
                        read_json_with_retry(manifest)
                    except (FileNotFoundError, PermissionError, json.JSONDecodeError) as error:
                        errors.append(error)
                        return

            thread = threading.Thread(target=reader, daemon=True)
            thread.start()
            for version in range(80):
                atomic_json_write(manifest, {"version": version})
            stop.set()
            thread.join(timeout=2)
            self.assertFalse(errors)
            self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))["version"], 79)

    def test_fen_dataset_is_resumable_and_verifiable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "games.pgn"
            source.write_text(GM_PGN, encoding="utf-8")
            output = root / "dataset"

            builder = FenDatasetBuilder(
                output,
                target_bytes=1024 * 1024,
                shard_bytes=32 * 1024,
                allowed_titles={"GM"},
                only_gm_actions=False,
            )
            first = builder.ingest_path(source, {"name": "local-test"})
            builder.close("COMPLETE")
            self.assertEqual(first["accepted"], 1)
            self.assertEqual(first["positions"], 6)
            self.assertEqual(command_verify(Namespace(fixture_only=True, output=str(output))), 0)

            shard = next((output / "shards").glob("*.jsonl"))
            row = json.loads(shard.read_text(encoding="utf-8").splitlines()[0])
            sample = row["positions"][0]
            self.assertEqual(len(sample["fen"].split()), 6)
            self.assertEqual(sample["action_uci"], "e2e4")
            self.assertEqual(sample["opponent_action_uci"], "e7e5")
            self.assertEqual(sample["outcome_pov"], 1)
            self.assertTrue(sample["actor_is_gm"])

            resumed = FenDatasetBuilder(
                output,
                target_bytes=1024 * 1024,
                shard_bytes=32 * 1024,
                allowed_titles={"GM"},
                only_gm_actions=False,
            )
            second = resumed.ingest_path(source, {"name": "local-test"})
            resumed.close("COMPLETE")
            self.assertEqual(second["duplicates"], 1)
            self.assertEqual(command_verify(Namespace(fixture_only=True, output=str(output))), 0)

    def test_resumable_downloader_uses_http_range(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), _RangeHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as temporary:
                destination = Path(temporary) / "archive.pgn"
                partial = destination.with_suffix(".pgn.part")
                partial.write_bytes(_RangeHandler.payload[:11])
                result = ResilientDownloader(timeout_seconds=5, retries=1).download(
                    f"http://127.0.0.1:{server.server_port}/archive.pgn",
                    destination,
                )
                self.assertEqual(destination.read_bytes(), _RangeHandler.payload)
                self.assertFalse(partial.exists())
                self.assertEqual(result.bytes_written, len(_RangeHandler.payload))
        finally:
            server.shutdown()
            server.server_close()

    def test_adversarial_jepa_trains_and_scores_response_branches(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "games.pgn"
            source.write_text(GM_PGN, encoding="utf-8")
            dataset = root / "dataset"
            builder = FenDatasetBuilder(
                dataset,
                target_bytes=1024 * 1024,
                shard_bytes=32 * 1024,
                allowed_titles={"GM"},
                only_gm_actions=False,
            )
            builder.ingest_path(source, {"name": "local-test"})
            builder.close("COMPLETE")
            game = next(iter_dataset_games(dataset))
            generator = np.random.default_rng(7)
            samples = [
                sample_from_dataset_position(position, generator)
                for position in game["positions"]
            ]
            samples = [item for item in samples if item is not None]
            model_path = root / "a_jepa_v7.npz"
            model = AdversarialJEPA(model_path, latent_size=16)
            metrics = model.train_batch(samples, learning_rate=0.001)
            self.assertTrue(all(np.isfinite(value) for value in metrics.values()))
            self.assertGreater(metrics["h2_coverage"], 0.0)
            self.assertGreater(metrics["h4_coverage"], 0.0)
            model.save()
            restored = AdversarialJEPA(model_path, create_if_missing=False)
            self.assertEqual(restored.trained_steps, 1)
            state = snapshot_from_fen(game["positions"][0]["fen"])
            engine = vitriengine(state, 0.02)
            legal = engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)[:3]
            _, priors, entropy = restored.score_legal_moves(state, legal)
            self.assertAlmostEqual(sum(priors), 1.0, places=5)
            self.assertTrue(np.isfinite(entropy))

            outputs = []
            worker = engineworker(
                state, 0.08, 17, threading.Event(),
                str(root / "missing_v6.npz"), None, str(model_path),
            )
            worker.ket_qua.connect(outputs.append)
            worker.chay()
            self.assertIn(outputs[0]["move"], engine.lay_tat_ca_nuoc_di_hop_le(engine.turn))
            self.assertEqual(outputs[0]["model_kind"], "A_JEPA_V7")

            baseline = DirectPolicyValueBaseline(root / "policy_value.npz", latent_size=16)
            baseline_metrics = baseline.train_batch(samples, learning_rate=0.001)
            self.assertTrue(all(np.isfinite(value) for value in baseline_metrics.values()))
            _, baseline_priors, _ = baseline.score_legal_moves(state, legal)
            self.assertAlmostEqual(sum(baseline_priors), 1.0, places=5)
            ranking = evaluate(dataset, model_path, "adversarial-jepa", "train", 0, 3, fixture_only=True)
            self.assertEqual(ranking["positions"], 3)
            self.assertTrue(np.isfinite(ranking["mean_nll"]))

    def test_v7_trainer_writes_fingerprinted_checkpoint_and_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "games.pgn"
            source.write_text(GM_PGN, encoding="utf-8")
            dataset = root / "dataset"
            builder = FenDatasetBuilder(
                dataset,
                target_bytes=1024 * 1024,
                shard_bytes=32 * 1024,
                allowed_titles={"GM"},
                only_gm_actions=False,
            )
            builder.ingest_path(source, {"name": "local-test"})
            builder.close("COMPLETE")
            model_path = root / "trained_v7.npz"
            result = train(Namespace(fixture_only=True,
                dataset=str(dataset), model=str(model_path), epochs=1,
                batch_size=2, learning_rate=0.001, latent_size=16,
                seed=9, validation_percent=1, max_train_batches=2,
                max_validation_batches=2, allow_dataset_change=False,
            ))
            self.assertEqual(result, 0)
            self.assertTrue(model_path.exists())
            report = json.loads(model_path.with_suffix(".training.json").read_text(encoding="utf-8"))
            self.assertEqual(len(report["epochs"]), 1)
            self.assertGreaterEqual(report["epochs"][0]["trained_steps"], 1)
            first_steps = report["trained_steps"]
            self.assertEqual(report["status"], "COMPLETE")
            resumed = train(Namespace(fixture_only=True,
                dataset=str(dataset), model=str(model_path), epochs=1,
                batch_size=2, learning_rate=0.001, latent_size=16,
                seed=9, validation_percent=1, max_train_batches=2,
                max_validation_batches=2, allow_dataset_change=False,
                resume=True, progress_interval=0.001,
            ))
            self.assertEqual(resumed, 0)
            resumed_report = json.loads(model_path.with_suffix(".training.json").read_text(encoding="utf-8"))
            self.assertEqual(resumed_report["completed_epochs"], 2)
            self.assertEqual(len(resumed_report["epochs"]), 2)
            self.assertGreater(resumed_report["trained_steps"], first_steps)
            manifest_path = dataset / "dataset_manifest.json"
            changed_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            changed_manifest["incremental_training_test"] = True
            manifest_path.write_text(json.dumps(changed_manifest), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                train(Namespace(fixture_only=True,
                    dataset=str(dataset), model=str(model_path), epochs=1,
                    batch_size=2, learning_rate=0.001, latent_size=16,
                    seed=9, validation_percent=1, max_train_batches=1,
                    max_validation_batches=1, allow_dataset_change=False,
                    resume=True, progress_interval=0.001,
                ))
            with self.assertRaisesRegex(ValueError, "overrides are disabled"):
                train(Namespace(fixture_only=True,
                    dataset=str(dataset), model=str(model_path), epochs=1,
                    batch_size=2, learning_rate=0.001, latent_size=16,
                    seed=9, validation_percent=1, max_train_batches=1,
                    max_validation_batches=1, allow_dataset_change=True,
                    resume=True, progress_interval=0.001,
                ))



if __name__ == "__main__":
    unittest.main(verbosity=2)
