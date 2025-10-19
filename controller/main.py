import os
import sys
import time
import json
import subprocess
from datetime import datetime, timezone
from .deps import ensure_uv, install_core_deps, install_open_writing_bench
from .db import make_engine, write_log_snapshot
from .command import build_bench_command
from .logstream import PipeAggregator

def main():
    db_url = os.environ.get("DATABASE_URL")
    run_key = os.environ.get("RUN_KEY")
    params = os.environ.get("SUBMISSION_PARAMS_JSON")
    owb_repo = os.environ.get("OWB_REPO")
    owb_ref = os.environ.get("OWB_REF")

    if not db_url or not run_key or not params or not owb_repo or not owb_ref:
        print("Missing required envs: DATABASE_URL, RUN_KEY, SUBMISSION_PARAMS_JSON, OWB_REPO, OWB_REF", file=sys.stderr)
        sys.exit(2)

    # 1) Ensure toolchain and deps
    ensure_uv()
    install_core_deps()
    install_open_writing_bench(owb_repo, owb_ref)

    # 2) Build command
    argv = build_bench_command(params, run_key)
    print(f"[controller] launching: {' '.join(argv)}", flush=True)

    # 3) Start process with pipes
    proc = subprocess.Popen(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace",
    )


    engine = make_engine(db_url)
    agg = PipeAggregator()
    agg.start(proc)

    last_flush = time.monotonic()
    FLUSH_EVERY = 30.0  # seconds

    rc = None
    try:
        while True:
            # Periodic flush
            now = time.monotonic()
            if now - last_flush >= FLUSH_EVERY:
                out_chunk = agg.drain_chunk(agg.q_out)
                err_chunk = agg.drain_chunk(agg.q_err)
                if out_chunk:
                    write_log_snapshot(engine, run_key, "stdout", out_chunk)
                if err_chunk:
                    write_log_snapshot(engine, run_key, "stderr", err_chunk)
                last_flush = now

            ret = proc.poll()
            if ret is not None:
                rc = ret
                # Final drain
                out_chunk = agg.drain_chunk(agg.q_out)
                err_chunk = agg.drain_chunk(agg.q_err)
                if out_chunk:
                    write_log_snapshot(engine, run_key, "stdout", out_chunk)
                if err_chunk:
                    write_log_snapshot(engine, run_key, "stderr", err_chunk)
                if ret != 0:
                    print(f"[controller] process exited with {ret}", file=sys.stderr, flush=True)
                break

            time.sleep(0.5)
    finally:
        try:
            proc.terminate()
        except Exception:
            pass

    sys.exit(rc if rc is not None else 1)

if __name__ == "__main__":
    main()
