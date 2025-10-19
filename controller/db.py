from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def make_engine(db_url: str):
    return create_engine(db_url, pool_pre_ping=True, future=True)

def write_log_snapshot(engine, run_key: str, stream: str, chunk: str):
    # Assumed schema:
    # CREATE TABLE run_logs (
    #   id BIGSERIAL PRIMARY KEY,
    #   run_key TEXT NOT NULL,
    #   ts TIMESTAMPTZ NOT NULL DEFAULT now(),
    #   stream TEXT NOT NULL CHECK (stream IN ('stdout','stderr')),
    #   data TEXT NOT NULL
    # );
    with engine.begin() as con:
        con.execute(
            text("INSERT INTO run_logs (run_key, stream, data) VALUES (:rk, :st, :data)"),
            {"rk": run_key, "st": stream, "data": chunk[-100000:]}  # cap a single insert
        )
