"""Small frozen entry point: divert multiprocessing before importing Qt."""
import multiprocessing
import os
import sys

if __name__ == "__main__":
    multiprocessing.freeze_support()
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    if "--self-test" in sys.argv:
        output = sys.argv[sys.argv.index("--self-test") + 1]
        try:
            from release_smoke import run
            code = run(output)
        except BaseException:
            import traceback
            from runtime_safety import atomic_json
            atomic_json(output, {"status": "FAILED", "stage": "bootstrap", "error": traceback.format_exc()})
            code = 1
        raise SystemExit(code)
    from main import run_application
    raise SystemExit(run_application())
