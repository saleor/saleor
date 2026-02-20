"""Generate a database schema snapshot from a specific git tag.

Creates a SQL file containing the full schema and django_migrations data
for a given release tag. This snapshot can then be loaded into empty databases
to skip running thousands of old migrations.

Usage:
    python manage.py generate_db_snapshot
    python manage.py generate_db_snapshot --tag 3.22.0
"""

import os
import shutil
import subprocess
import tempfile
from urllib.parse import urlparse

from django.core.management.base import BaseCommand, CommandError

from ....db_snapshot import SNAPSHOT_VERSION
from ....db_snapshot.utils import SNAPSHOT_PATH

TEMP_DB_NAME = "saleor_snapshot_temp"


class Command(BaseCommand):
    help = "Generate a DB schema snapshot from a release tag."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tag",
            default=SNAPSHOT_VERSION,
            help=f"Git tag to generate snapshot from (default: {SNAPSHOT_VERSION})",
        )
        parser.add_argument(
            "--db-url",
            default="postgres://saleor:saleor@localhost:5432",
            help="PostgreSQL server URL (without database name)",
        )

    def handle(self, **options):
        tag = options["tag"]
        db_url = options["db_url"].rstrip("/")
        parsed = urlparse(db_url)
        self._pg_env = {
            "PGHOST": parsed.hostname or "localhost",
            "PGPORT": str(parsed.port or 5432),
            "PGUSER": parsed.username or "saleor",
            "PGPASSWORD": parsed.password or "",
        }
        worktree_dir = None

        try:
            self._verify_tools()

            self.stdout.write(f"Creating temporary database {TEMP_DB_NAME}...")
            self._pg_run(["dropdb", "--if-exists", "-f", TEMP_DB_NAME])
            self._pg_run(["createdb", TEMP_DB_NAME])

            worktree_dir = tempfile.mkdtemp(prefix="saleor_snapshot_")
            self.stdout.write(f"Creating git worktree at tag {tag}...")
            self._run(["git", "worktree", "add", "--detach", worktree_dir, tag])

            self.stdout.write("Running migrations from tag...")
            self._run(
                ["python", "manage.py", "migrate", "--no-input"],
                cwd=worktree_dir,
                env_override={
                    "DATABASE_URL": f"{db_url}/{TEMP_DB_NAME}",
                },
            )

            self.stdout.write(f"Dumping snapshot to {SNAPSHOT_PATH}...")
            SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)

            schema_sql = self._pg_capture(
                [
                    "pg_dump",
                    "--schema-only",
                    "--no-owner",
                    "--no-privileges",
                    TEMP_DB_NAME,
                ]
            )
            migrations_sql = self._pg_capture(
                [
                    "pg_dump",
                    "--data-only",
                    "--table=django_migrations",
                    "--no-owner",
                    "--no-privileges",
                    TEMP_DB_NAME,
                ]
            )

            snapshot = schema_sql + "\n" + migrations_sql
            # Strip SET commands for parameters that only exist in newer PG
            # versions — the dump tool may be newer than the target server.
            snapshot = self._strip_incompatible_set_commands(snapshot)
            SNAPSHOT_PATH.write_text(snapshot)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Snapshot generated: {SNAPSHOT_PATH} "
                    f"({SNAPSHOT_PATH.stat().st_size:,} bytes)"
                )
            )
        finally:
            self.stdout.write("Cleaning up...")
            try:
                self._pg_run(["dropdb", "--if-exists", "-f", TEMP_DB_NAME])
            except CommandError:
                pass
            if worktree_dir:
                try:
                    self._run(["git", "worktree", "remove", "--force", worktree_dir])
                except CommandError:
                    pass
                shutil.rmtree(worktree_dir, ignore_errors=True)

    @staticmethod
    def _strip_incompatible_set_commands(sql):
        """Remove SET commands for PG parameters that may not exist on older servers."""
        # pg_dump from a newer version may emit SET commands for parameters
        # that don't exist on the target server (e.g. transaction_timeout is
        # PG 17+ only).
        import re

        return re.sub(r"^SET transaction_timeout = \d+;\n", "", sql, flags=re.MULTILINE)

    def _verify_tools(self):
        for tool in ["git", "createdb", "dropdb", "pg_dump"]:
            if not shutil.which(tool):
                raise CommandError(f"Required tool not found: {tool}")

    def _run(self, cmd, cwd=None, env_override=None):
        env = os.environ.copy()
        if env_override:
            env.update(env_override)
        result = subprocess.run(
            cmd, cwd=cwd, env=env, capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            raise CommandError(
                f"Command failed: {' '.join(cmd)}\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )

    def _pg_run(self, cmd, **kwargs):
        """Run a command with PostgreSQL connection env vars."""
        env_override = kwargs.pop("env_override", {})
        env_override.update(self._pg_env)
        self._run(cmd, env_override=env_override, **kwargs)

    def _pg_capture(self, cmd):
        """Run a command with PostgreSQL env vars and return stdout."""
        env = os.environ.copy()
        env.update(self._pg_env)
        result = subprocess.run(
            cmd, env=env, capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            raise CommandError(
                f"Command failed: {' '.join(cmd)}\nstderr: {result.stderr}"
            )
        return result.stdout
