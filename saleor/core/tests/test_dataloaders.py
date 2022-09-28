from django.core.handlers.base import BaseHandler

from ...graphql.plugins.dataloaders import load_plugin_manager
from ..jwt import create_access_token


def test_plugins_manager_loader_loads_requestor_in_plugin(rf, customer_user, settings):
    settings.PLUGINS = ["saleor.plugins.tests.sample_plugins.ActivePlugin"]
    request = rf.request()
    token = create_access_token(customer_user)
    request.META["HTTP_AUTHORIZATION"] = f"JWT {token}"

    handler = BaseHandler()
    handler.load_middleware()
    handler.get_response(request)
    manager = load_plugin_manager(request)
    plugin = manager.all_plugins.pop()

    assert isinstance(plugin.requestor, type(customer_user))
    assert plugin.requestor.id == customer_user.id


def test_plugins_manager_loader_requestor_in_plugin_when_no_app_and_user_in_req_is_none(
    rf, settings
):
    settings.PLUGINS = ["saleor.plugins.tests.sample_plugins.ActivePlugin"]
    request = rf.request()

    handler = BaseHandler()
    handler.load_middleware()
    handler.get_response(request)
    manager = load_plugin_manager(request)
    plugin = manager.all_plugins.pop()

    assert not plugin.requestor
