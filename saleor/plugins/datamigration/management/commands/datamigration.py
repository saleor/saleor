from django.core.management import BaseCommand

from saleor.plugins.datamigration.management.commands.utils import DataMigration


class Command(BaseCommand):
    help = "Migrate data from old database to new one"

    def add_arguments(self, parser):
        parser.add_argument("url", type=str)
        parser.add_argument("token", type=str)

    def handle(self, *args, **options):

        # Migrate users data
        DataMigration().migrate(url=options["url"], token=options["token"])
        self.stdout.write(self.style.SUCCESS("Successfully migrated users data"))
