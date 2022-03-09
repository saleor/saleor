from ...graphql.views import GraphQLView
from ..base_plugin import BasePlugin
from .graphql.schema import schema


class VendorPlugin(BasePlugin):
    name = "vendor"
    PLUGIN_ID = "vendor"
    PLUGIN_NAME = "vendor"
    DEFAULT_ACTIVE = True
    CONFIGURATION_PER_CHANNEL = False

    def webhook(self, request, path, previous_value):
        view = GraphQLView.as_view(schema=schema)
        request.app = self
        return view(request)
