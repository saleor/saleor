from django.core.management.base import BaseCommand

from ...stock import remove_expired_reservations


class Command(BaseCommand):
    help = "Removes expired stock reservations from the database."

    def handle(self, *args, **options):
        remove_expired_reservations()
        self.stdout.write("Removed expired stock reservations.")
