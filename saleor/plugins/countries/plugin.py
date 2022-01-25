from ...graphql.views import GraphQLView
from ..base_plugin import BasePlugin
from .graphql.schema import schema


class CountriesPlugin(BasePlugin):
    PLUGIN_ID = "countries"
    PLUGIN_NAME = "Countries"
    DEFAULT_ACTIVE = True
    PLUGIN_DESCRIPTION = "A plugin for handling providing addresses data"
    CONFIGURATION_PER_CHANNEL = False

    def webhook(self, request, path, previous_value):
        request.app = self
        view = GraphQLView.as_view(schema=schema)
        return view(request)
