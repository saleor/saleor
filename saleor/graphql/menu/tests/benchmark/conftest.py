import pytest

from saleor.menu.utils import update_menu


@pytest.fixture
def site_with_top_menu(site_settings):
    menu = site_settings.top_menu
    menu.items.create(name="Link 1", url="http://example.com/")
    menu.items.create(name="Link 2", url="http://example.com/")
    menu.items.create(name="Link 3", url="http://example.com/")
    update_menu(menu)
    return site_settings


@pytest.fixture
def site_with_bottom_menu(site_settings):
    menu = site_settings.bottom_menu
    menu.items.create(name="Link 1", url="http://example.com/")
    menu.items.create(name="Link 2", url="http://example.com/")
    menu.items.create(name="Link 3", url="http://example.com/")
    update_menu(menu)
    return site_settings
