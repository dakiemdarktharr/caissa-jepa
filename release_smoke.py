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
    from PySide6.QtGui import QImage, QColor
    from PySide6.QtSvg import QSvgRenderer
    from main import boardwidget, monitor_window, application_resource_dir, modelmatchworker
    from model_registry import training_model_specs
    from fen_dataset_tool import FenDatasetBuilder
    from train_caissa_v7 import train
    from image_zip_import import zipimageimportworker
    from runtime_safety import atomic_json
    receipt = {"status": "FAILED", "checks": [], "frozen": bool(getattr(__import__("sys"), "frozen", False))}
    app = QApplication.instance() or QApplication([])
    try:
        with tempfile.TemporaryDirectory(prefix="caissa-release-") as folder:
            root = Path(folder)
            pgn = root / "smoke.pgn"
            pgn.write_text('[Event "Release fixture"]\n[White "Alpha"]\n[Black "Beta"]\n[WhiteTitle "GM"]\n[Result "1-0"]\n\n1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 1-0\n', encoding="utf-8")
            dataset = root / "fen_dataset"
            builder = FenDatasetBuilder(dataset, target_bytes=1024*1024, shard_bytes=32768,
                                        allowed_titles={"GM"}, only_gm_actions=False)
            builder.ingest_path(pgn, {"name": "release-fixture"})
            builder.close("COMPLETE")
            for spec in training_model_specs(root):
                args = Namespace(dataset=str(dataset), model=str(spec["path"]), architecture=spec["architecture"],
                    model_variant=spec["variant"], epochs=1, batch_size=4, latent_size=8,
                    learning_rate=5e-4, seed=20260903, validation_percent=10, max_train_batches=1,
                    max_validation_batches=1, resume=False, allow_dataset_change=False,
                    progress_interval=.1, cache_workers=2, time_budget_hours=.1)
                train(args)
                args.resume = True
                train(args)
                report = json.loads(spec["path"].with_suffix(".training.json").read_text(encoding="utf-8"))
                assert report["completed_epochs"] == 2 and report["status"] == "COMPLETE"
                receipt["checks"].append("train/resume " + spec["id"])
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
