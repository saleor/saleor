from django.core.management.base import BaseCommand
from saleor.plugins.manager import PluginsManager
from saleor.plugins.allegroSync.plugin import AllegroSyncPlugin


class Command(BaseCommand):
    version = "1.0"

    def add_arguments(self, parser):
        parser.add_argument('--pass', type=str, help='password for sender')

    def handle(self, *args, **options):
        manage = PluginsManager(plugins=["saleor.plugins.allegroSync.plugin.AllegroSyncPlugin"])
        plugin = manage.get_plugin(AllegroSyncPlugin.PLUGIN_ID)
        plugin.password = options['pass']
        plugin.synchronize_allegro_offers()
