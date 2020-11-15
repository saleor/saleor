from django.core.management.base import BaseCommand
from saleor.plugins.allegroSync.plugin import AllegroSyncPlugin


class Command(BaseCommand):
    version = "1.0"

    def handle(self, *args, **options):
        AllegroSyncPlugin.synchronize_allegro_offers()
