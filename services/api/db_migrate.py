"""Applies db/migrations/*.sql in order. No migration framework: the files are
small and numbered, and re-running is safe because every statement is wrapped
so an already-applied migration is skipped rather than erroring."""

import pathlib

from sqlalchemy import text

from db import engine

MIGRATIONS_DIR = pathlib.Path(__file__).parent / "db" / "migrations"


def main():
    applied = set()
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS schema_migrations (filename TEXT PRIMARY KEY, applied_at TIMESTAMPTZ DEFAULT now())"
            )
        )
        for row in conn.execute(text("SELECT filename FROM schema_migrations")):
            applied.add(row[0])

    for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if sql_file.name in applied:
            continue
        print(f"applying {sql_file.name}")
        sql = sql_file.read_text()
        with engine.begin() as conn:
            conn.execute(text(sql))
            conn.execute(
                text("INSERT INTO schema_migrations (filename) VALUES (:f)"),
                {"f": sql_file.name},
            )

    print("migrations up to date")


if __name__ == "__main__":
    main()
