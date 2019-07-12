import pytest

from saleor.core.extensions.checks import check_extensions


@pytest.mark.parametrize(
    "manager_path", [None, "", "saleor.core.extension.wrong_path.Manager"]
)
def test_check_extensions_missing_manager(manager_path, settings):
    settings.EXTENSIONS_MANAGER = manager_path
    errors = check_extensions({})
    assert errors


@pytest.mark.parametrize(
    "plugin_path", [None, "", "saleor.core.extension.wrong_path.Plugin"]
)
def test_check_extensions_plugins(plugin_path, settings):
    settings.PLUGINS = [plugin_path]
    errors = check_extensions({})
    assert errors
