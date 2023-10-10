from unittest.mock import call, patch

from django.utils.functional import SimpleLazyObject, empty

from ....graphql.core import SaleorContext
from ..dataloaders import plugin_manager_promise


@patch("saleor.graphql.plugins.dataloaders.PluginManagerByRequestorDataloader")
@patch("saleor.graphql.plugins.dataloaders.AnonymousPluginManagerLoader")
def test_plugin_manager_promise_no_requestor(
    mock_AnonymousPluginManagerLoader, mock_PluginManagerByRequestorDataloader
):
    # given
    mock_AnonymousPluginManagerLoader.return_value.load.return_value = "test anonymous"
    mock_PluginManagerByRequestorDataloader.return_value.load.return_value = (
        "test plugin manager"
    )
    user = SimpleLazyObject(lambda: None)
    assert user._wrapped is empty
    context = SaleorContext()
    context.user = user

    # when
    result = plugin_manager_promise(context, None)

    # then
    assert result == "test anonymous"
    assert user._wrapped is None
    assert mock_AnonymousPluginManagerLoader.mock_calls == [
        call(context),
        call().load("Anonymous"),
    ]
    assert mock_PluginManagerByRequestorDataloader.mock_calls == []


@patch("saleor.graphql.plugins.dataloaders.PluginManagerByRequestorDataloader")
@patch("saleor.graphql.plugins.dataloaders.AnonymousPluginManagerLoader")
def test_plugin_manager_promise_requestor_lazy_user(
    mock_AnonymousPluginManagerLoader, mock_PluginManagerByRequestorDataloader
):
    # given
    mock_AnonymousPluginManagerLoader.return_value.load.return_value = "test anonymous"
    mock_PluginManagerByRequestorDataloader.return_value.load.return_value = (
        "test plugin manager"
    )
    user = SimpleLazyObject(lambda: "test user")
    assert user._wrapped is empty
    context = SaleorContext()
    context.user = user

    # when
    result = plugin_manager_promise(context, None)

    # then
    assert result == "test plugin manager"
    assert user._wrapped == "test user"
    assert mock_AnonymousPluginManagerLoader.mock_calls == []
    assert mock_PluginManagerByRequestorDataloader.mock_calls == [
        call(context),
        call().load("test user"),
    ]


@patch("saleor.graphql.plugins.dataloaders.PluginManagerByRequestorDataloader")
@patch("saleor.graphql.plugins.dataloaders.AnonymousPluginManagerLoader")
def test_plugin_manager_promise_requestor_is_app(
    mock_AnonymousPluginManagerLoader, mock_PluginManagerByRequestorDataloader
):
    # given
    mock_AnonymousPluginManagerLoader.return_value.load.return_value = "test anonymous"
    mock_PluginManagerByRequestorDataloader.return_value.load.return_value = (
        "test plugin manager"
    )
    app = SimpleLazyObject(lambda: "test user")
    assert app._wrapped is empty
    context = SaleorContext()
    context.user = app

    # when
    result = plugin_manager_promise(context, "test app")

    # then
    assert result == "test plugin manager"
    assert app._wrapped is empty
    assert mock_AnonymousPluginManagerLoader.mock_calls == []
    assert mock_PluginManagerByRequestorDataloader.mock_calls == [
        call(context),
        call().load("test app"),
    ]
