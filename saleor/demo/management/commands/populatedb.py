from django.conf import settings

from ....channel.models import Channel
from ....core.management.commands.populatedb import Command as PopulateDBCommand
from ....payment.gateways.braintree.plugin import BraintreeGatewayPlugin
from ....plugins.manager import get_plugins_manager


def configure_braintree():
    braintree_api_key = getattr(settings, "BRAINTREE_API_KEY", "")
    braintree_merchant_id = getattr(settings, "BRAINTREE_MERCHANT_ID", "")
    braintree_secret = getattr(settings, "BRAINTREE_SECRET_API_KEY", "")

    if not (braintree_api_key and braintree_merchant_id and braintree_secret):
        return False

    channels = Channel.objects.all()
    manager = get_plugins_manager()
    for channel in channels:
        manager.save_plugin_configuration(
            BraintreeGatewayPlugin.PLUGIN_ID,
            channel.slug,
            {
                "active": True,
                "configuration": [
                    {"name": "Public API key", "value": braintree_api_key},
                    {"name": "Merchant ID", "value": braintree_merchant_id},
                    {"name": "Secret API key", "value": braintree_secret},
                    {"name": "Use sandbox", "value": True},
                ],
            },
        )
    return True


class Command(PopulateDBCommand):
    def handle(self, *args, **options):
        super().handle(*args, **options)
        is_configured = configure_braintree()
        if is_configured:
            self.stdout.write("Configured Braintree")
        else:
            self.stdout.write(
                "Failed to configure Braintree. Check if proper environment variables "
                "are set."
            )
