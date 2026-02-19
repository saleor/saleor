import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

SNAPSHOT_PATH = Path(__file__).parent / "snapshot.sql"


def has_snapshot() -> bool:
    return SNAPSHOT_PATH.exists()


def is_database_empty(connection) -> bool:
    """Check if the database has no Django tables (i.e. is a fresh empty DB)."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT EXISTS ("
            "  SELECT FROM information_schema.tables"
            "  WHERE table_schema = 'public'"
            "  AND table_name = 'django_migrations'"
            ")"
        )
        return not cursor.fetchone()[0]


def load_snapshot(connection) -> None:
    """Load the snapshot SQL into the database using psql.

    Uses psql instead of cursor.execute() because pg_dump output may contain
    COPY commands and version-specific SET parameters that aren't compatible
    with a plain cursor.execute() call.
    """
    db_settings = connection.settings_dict
    env = os.environ.copy()
    env["PGPASSWORD"] = db_settings.get("PASSWORD", "")

    cmd = [
        "psql",
        "-h",
        db_settings.get("HOST", "localhost"),
        "-p",
        str(db_settings.get("PORT", 5432)),
        "-U",
        db_settings.get("USER", "saleor"),
        "-d",
        db_settings["NAME"],
        "-v",
        "ON_ERROR_STOP=1",
        "-f",
        str(SNAPSHOT_PATH),
    ]

    logger.info("Loading DB snapshot from %s via psql", SNAPSHOT_PATH)
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to load snapshot via psql:\n{result.stderr}")
    logger.info("Snapshot loaded successfully.")
