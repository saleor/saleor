from ...graphql.views import GraphQLView
from ..base_plugin import BasePlugin
from .graphql.schema import schema


class OTPPlugin(BasePlugin):
    name = "OTP"  # tackle saleor#8873
    PLUGIN_ID = "otp"
    PLUGIN_NAME = "OTP"
    DEFAULT_ACTIVE = True
    PLUGIN_DESCRIPTION = "Plugin for handling providing OTPs for emails"
    CONFIGURATION_PER_CHANNEL = False

    def webhook(self, request, path, previous_value):
        request.app = self
        view = GraphQLView.as_view(schema=schema)
        return view(request)
