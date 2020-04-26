import pytest

from saleor.plugins.checks import check_plugins


@pytest.mark.parametrize(
    "manager_path", [None, "", "saleor.core.plugins.wrong_path.Manager"]
)
def test_check_plugins_missing_manager(manager_path, settings):
    settings.PLUGINS_MANAGER = manager_path
    errors = check_plugins({})
    assert errors


@pytest.mark.parametrize(
    "plugin_path", [None, "", "saleor.core.plugins.wrong_path.Plugin"]
)
def test_check_plugins_wrong_declaration_of_plugins(plugin_path, settings):
    settings.PLUGINS = [plugin_path]
    errors = check_plugins({})
    assert errors
