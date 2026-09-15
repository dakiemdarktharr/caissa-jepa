"""Source/frozen smoke test using temporary data only; emits a JSON receipt."""
import json
import os
import tempfile
import threading
import traceback
import zipfile
from argparse import Namespace
from pathlib import Path


def run(output):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QImage, QColor, QFontDatabase
    from PySide6.QtSvg import QSvgRenderer
    from main import boardwidget, monitor_window, application_resource_dir, modelmatchworker
    from model_registry import training_model_specs
    from fen_dataset_tool import FenDatasetBuilder
    from train_caissa_v7 import train
    from image_zip_import import zipimageimportworker
    from runtime_safety import atomic_json
    receipt = {"status": "FAILED", "checks": [], "frozen": bool(getattr(__import__("sys"), "frozen", False))}
    app = QApplication.instance() or QApplication([])
    if os.name == "nt":
        for name in ("consola.ttf", "consolab.ttf", "segoeui.ttf"):
            font = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / name
            if font.exists():
                QFontDatabase.addApplicationFont(str(font))
    try:
        with tempfile.TemporaryDirectory(prefix="caissa-release-") as folder:
            root = Path(folder)
            pgn = root / "smoke.pgn"
            pgn.write_text('[Event "Release fixture"]\n[White "Alpha"]\n[Black "Beta"]\n[WhiteTitle "GM"]\n[Result "1-0"]\n\n1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 1-0\n', encoding="utf-8")
            fixture_text = pgn.read_text(encoding="utf-8")
            pgn.write_text("\n".join(fixture_text.replace('[Event "Release fixture"]', f'[Event "Release fixture {i}"]') for i in range(24)), encoding="utf-8")
            dataset = root / "fen_dataset"
            builder = FenDatasetBuilder(dataset, target_bytes=1024*1024, shard_bytes=32768,
                                        allowed_titles={"GM"}, only_gm_actions=False)
            builder.ingest_path(pgn, {"name": "release-fixture"})
            builder.close("COMPLETE")
            dataset_alias = dataset
            if os.name == "nt":
                import _winapi
                dataset_alias = root / "dataset-junction"
                _winapi.CreateJunction(str(dataset), str(dataset_alias))
            # Source and frozen must both normalize a real Windows junction.
            from training_runtime import SampleCache
            from adversarial_jepa import dataset_manifest_fingerprint
            cache = SampleCache(dataset_alias, dataset_manifest_fingerprint(dataset_alias), 10, workers=1).prepare()
            assert cache.path.parent == dataset.resolve()
            assert cache.counts["train"] > 0 and cache.counts["validation"] > 0
            receipt["checks"].append("junction cache path + nonempty training/validation splits")
            for spec in training_model_specs(root):
                args = Namespace(fixture_only=True, dataset=str(dataset_alias), model=str(spec["path"]), architecture=spec["architecture"],
                    model_variant=spec["variant"], epochs=1, batch_size=4, latent_size=8,
                    learning_rate=5e-4, seed=20260903, validation_percent=10, max_train_batches=1,
                    max_validation_batches=1, resume=False, allow_dataset_change=False,
                    progress_interval=.1, cache_workers=2, time_budget_hours=.1)
                train(args)
                args.resume = True
                train(args)
                report = json.loads(spec["path"].with_suffix(".training.json").read_text(encoding="utf-8"))
                assert report["completed_epochs"] == 2 and report["status"] == "COMPLETE"
                assert report["validation_available"] and report["epochs"][-1]["validation"]
                receipt["checks"].append("train/resume " + spec["id"])
            # A same-size damaged cache must recover in a packaged worker, too.
            bad = cache.path / "shard_00000.bin"
            expected = bad.read_bytes()
            damaged = bytearray(expected)
            damaged[-1] ^= 1
            bad.write_bytes(damaged)
            SampleCache(dataset_alias, dataset_manifest_fingerprint(dataset_alias), 10, workers=1).prepare()
            assert bad.read_bytes() == expected
            receipt["checks"].append("same-length cache corruption recovered")
            # Reproduce the original collision using temporary data; require a full report.
            probe = root / "failure.npz"
            failure_args = Namespace(**vars(args))
            failure_args.model, failure_args.resume = str(probe), False
            probe.with_suffix(".generations").write_text("collision", encoding="utf-8")
            try:
                train(failure_args)
                raise AssertionError("Generation collision should fail")
            except FileExistsError:
                failure = json.loads(probe.with_suffix(".training.json").read_text(encoding="utf-8"))
                assert "checkpoint_commit" in failure["traceback"] and "path_diagnostics" in failure
            receipt["checks"].append("startup collision traceback and resolved paths")
            if dataset_alias != dataset:
                os.rmdir(dataset_alias)  # Remove only the temporary junction, never its target.
            board = boardwidget(project_dir=root)
            for piece, filename in board.piece_to_file.items():
                renderer = QSvgRenderer(str(application_resource_dir() / "assets/chess_pieces" / filename))
                assert renderer.isValid(), filename
                board.piece_renderers[piece] = renderer
            monitor = monitor_window(board)
            monitor.resize(1400, 950)
            monitor.show()
            app.processEvents()
            assert not monitor.grab().isNull()
            screenshot = Path(output).with_suffix(".png")
            screenshot.parent.mkdir(parents=True, exist_ok=True)
            monitor.grab().save(str(screenshot))
            monitor.close()
            board.clock_timer.stop()
            board.close()
            receipt["checks"].append("Qt monitor and bundled SVG assets")
            image = QImage(8, 8, QImage.Format_RGB32)
            image.fill(QColor("red"))
            image.save(str(root / "valid.png"))
            with zipfile.ZipFile(root / "images.zip", "w") as archive:
                archive.write(root / "valid.png", "nested/valid.png")
                archive.writestr("nested/data:payload.png", b"invalid")
                archive.writestr("broken.png", b"not an image")
            results = []
            worker = zipimageimportworker([root / "images.zip"], dataset, threading.Event())
            worker.ket_qua.connect(results.append)
            worker.chay()
            assert results[0]["imported"] == 1 and results[0]["errors"] == 1 and results[0]["skipped"] == 1, results
            receipt["checks"].append("ZIP decode/path validation and image staging")
            results = []
            arena = modelmatchworker(root, root / "book.sqlite", "alpha-beta", "a-jepa-h1",
                threading.Event(), move_time=.02, max_plies=14, forced_match_seed=9)
            arena.ket_qua.connect(results.append)
            arena.chay()
            assert len(results) == 1 and "error" not in results[0], results
            assert results[0]["plies"] == 14 and results[0]["opening_plies"] == 12
            receipt["checks"].append("arena frozen opening + learned moves + JSONL/PGN persistence")
        receipt["status"] = "PASSED"
    except BaseException:
        receipt["error"] = traceback.format_exc()
    atomic_json(Path(output), receipt)
    return 0 if receipt["status"] == "PASSED" else 1


if __name__ == "__main__":
    __import__("multiprocessing").freeze_support()
    raise SystemExit(run(__import__("sys").argv[1]))
