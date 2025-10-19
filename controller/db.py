from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def make_engine(db_url: str):
    return create_engine(db_url, pool_pre_ping=True, future=True)

def write_log_snapshot(engine, run_key: str, stream: str, chunk: str):
    """
    Append `chunk` to the single (run_key, stream) row.
    If no row exists, insert one. Cap stored data to last 100k chars.
    Works on Postgres and SQLite.
    """
    CAP = 100_000
    data = (chunk or "")[-CAP:]

    dialect = engine.dialect.name  # 'postgresql' | 'sqlite' | ...

    if dialect == "postgresql":
        # right(x, n) is portable on Postgres
        update_sql = text("""
            UPDATE run_logs
               SET data = RIGHT(run_logs.data || :data, :cap),
                   ts   = now()
             WHERE run_key = :rk AND stream = :st
        """)
        insert_sql = text("""
            INSERT INTO run_logs (run_key, stream, data)
            VALUES (:rk, :st, :data)
        """)
        params = {"rk": run_key, "st": stream, "data": data, "cap": CAP}

    else:
        # SQLite: use substr(x, -n) for "last n"
        update_sql = text("""
            UPDATE run_logs
               SET data = substr(run_logs.data || :data, -:cap),
                   ts   = CURRENT_TIMESTAMP
             WHERE run_key = :rk AND stream = :st
        """)
        insert_sql = text("""
            INSERT INTO run_logs (run_key, stream, data)
            VALUES (:rk, :st, :data)
        """)
        params = {"rk": run_key, "st": stream, "data": data, "cap": CAP}

    with engine.begin() as con:
        res = con.execute(update_sql, params)
        if res.rowcount == 0:
            con.execute(insert_sql, params)
