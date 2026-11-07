import asyncio

import asyncpg

from src.core.config import settings


async def detect_migration_mode() -> str:
    connection = await asyncpg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASS,
        database=settings.DB_NAME,
    )
    try:
        rows = await connection.fetch(
            "SELECT tablename FROM pg_tables "
            "WHERE schemaname = 'public' "
            "AND tablename IN ('users', 'alembic_version')"
        )
        tables = {row["tablename"] for row in rows}

        if "users" not in tables:
            return "upgrade"
        if "alembic_version" not in tables:
            return "stamp"

        revisions = await connection.fetchval("SELECT count(*) FROM alembic_version")
        return "upgrade" if revisions else "stamp"
    finally:
        await connection.close()


def main() -> None:
    print(asyncio.run(detect_migration_mode()))


if __name__ == "__main__":
    main()
