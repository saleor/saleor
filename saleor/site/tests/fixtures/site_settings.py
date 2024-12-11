import pytest

from ....menu.models import Menu
from ...models import Site, SiteSettings


@pytest.fixture(autouse=True)
def site_settings(db, settings) -> SiteSettings:
    """Create a site and matching site settings.

    This fixture is autouse because django.contrib.sites.models.Site and
    saleor.site.models.SiteSettings have a one-to-one relationship and a site
    should never exist without a matching settings object.
    """
    site = Site.objects.get_or_create(name="mirumee.com", domain="mirumee.com")[0]
    obj = SiteSettings.objects.get_or_create(
        site=site,
        default_mail_sender_name="Mirumee Labs",
        default_mail_sender_address="mirumee@example.com",
    )[0]
    settings.SITE_ID = site.pk
    settings.ALLOWED_HOSTS += [site.domain]

    main_menu = Menu.objects.get_or_create(
        name=settings.DEFAULT_MENUS["top_menu_name"],
        slug=settings.DEFAULT_MENUS["top_menu_name"],
    )[0]
    secondary_menu = Menu.objects.get_or_create(
        name=settings.DEFAULT_MENUS["bottom_menu_name"],
        slug=settings.DEFAULT_MENUS["bottom_menu_name"],
    )[0]
    obj.top_menu = main_menu
    obj.bottom_menu = secondary_menu
    obj.save()
    return obj


@pytest.fixture
def site_settings_with_reservations(site_settings):
    site_settings.reserve_stock_duration_anonymous_user = 5
    site_settings.reserve_stock_duration_authenticated_user = 5
    site_settings.save()
    return site_settings
