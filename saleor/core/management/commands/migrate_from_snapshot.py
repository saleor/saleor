"""Run migrations using a pre-built schema snapshot when possible.

For empty databases, loads the snapshot first then applies only the
migrations added after the snapshot version. For non-empty databases,
runs standard Django migrate.

Usage:
    python manage.py migrate_from_snapshot
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connections

from ....db_snapshot.utils import has_snapshot, is_database_empty, load_snapshot


class Command(BaseCommand):
    help = "Migrate using a DB snapshot for empty databases."

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default="default",
            help="Database alias to migrate (default: default)",
        )

    def handle(self, **options):
        database = options["database"]
        connection = connections[database]
        verbosity = options["verbosity"]

        if is_database_empty(connection):
            if has_snapshot():
                self.stdout.write("Empty database detected. Loading snapshot...")
                load_snapshot(connection)
                self.stdout.write(
                    self.style.SUCCESS(
                        "Snapshot loaded. Running remaining migrations..."
                    )
                )
            else:
                self.stdout.write(
                    "Empty database detected but no snapshot found. "
                    "Running full migration..."
                )
        else:
            self.stdout.write(
                "Database has existing tables. Running incremental migrate..."
            )

        call_command("migrate", database=database, verbosity=verbosity)
        self.stdout.write(self.style.SUCCESS("Migration complete."))
