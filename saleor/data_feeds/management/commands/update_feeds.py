from django.core.management import BaseCommand

from ...google_merchant import update_feed


class Command(BaseCommand):
    help = "Update Google merchant feed"

    def handle(self, *args, **options):
        update_feed()
