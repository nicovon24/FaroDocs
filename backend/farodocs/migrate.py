"""Apply ordered PostgreSQL migrations once, inside a transaction."""

import os
from importlib.resources import files

import psycopg


def main() -> None:
    database_url = os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://", 1)
    migrations = sorted(files("farodocs.sql").iterdir(), key=lambda path: path.name)

    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
            )
            cursor.execute("SELECT pg_advisory_xact_lock(7418060)")
            cursor.execute("SELECT name FROM schema_migrations")
            applied = {row[0] for row in cursor.fetchall()}
            for migration in migrations:
                if migration.suffix != ".sql" or migration.name in applied:
                    continue
                cursor.execute(migration.read_text(encoding="utf-8"))
                cursor.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (migration.name,))
                print(f"Applied {migration.name}")


if __name__ == "__main__":
    main()
