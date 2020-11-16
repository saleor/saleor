from django.core.management.base import BaseCommand
from saleor.plugins.manager import PluginsManager
from saleor.plugins.allegroSync.plugin import AllegroSyncPlugin


class Command(BaseCommand):
    version = "1.0"

    def handle(self, *args, **options):
        manage = PluginsManager(plugins=["saleor.plugins.allegroSync.plugin.AllegroSyncPlugin"])
        plugin = manage.get_plugin(AllegroSyncPlugin.PLUGIN_ID)
        plugin.synchronize_allegro_offers()
