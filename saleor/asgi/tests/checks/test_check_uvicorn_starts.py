import re
from unittest.mock import Mock

import pytest
import requests
from django.contrib.sites.models import Site

from saleor.site.models import SiteSettings

from .check_uvicorn_starts import check_response, initialize_site


def test_initialize_site_rejects_when_debug_mode_disabled(settings):
    # given
    settings.DEBUG = False

    # when/when
    with pytest.raises(AssertionError, match="Cannot run this file without DEBUG=true"):
        initialize_site()

    # Sanity check: should work fine when `True`
    settings.DEBUG = True
    initialize_site()


def test_initialize_site_recreates_site_and_settings(settings):
    """When Site is deleted, then it should recreate it.

    This is needed due to some test cases deleting the Site object which means
    the GitHub Workflow that run `check_uvicorn_starts` must recreate it.
    """
    settings.DEBUG = True

    # given
    qs_site = Site.objects.filter(pk=settings.SITE_ID)
    qs_site_settings = SiteSettings.objects.filter(site_id=settings.SITE_ID)
    assert qs_site.delete()

    Site.objects.clear_cache()
    assert qs_site.exists() is False
    assert qs_site_settings.exists() is False

    # when
    initialize_site()

    # then
    site = qs_site.get()
    site_settings = qs_site_settings.get()
    assert site.domain == "example.com"
    assert site_settings.site_id == site.pk


def test_initialize_site_does_not_recreate_when_exists(settings):
    """When Site is exists, then it should not attempt to recreate it."""
    settings.DEBUG = True

    # given
    qs_site = Site.objects.filter(pk=settings.SITE_ID)
    qs_site_settings = SiteSettings.objects.filter(site_id=settings.SITE_ID)
    assert qs_site.exists() is True

    Site.objects.clear_cache()

    # when
    initialize_site()

    # then (unchanged)
    site = qs_site.get()
    site_settings = qs_site_settings.get()
    assert site.domain == "example.com"
    assert site_settings.site_id == site.pk


@pytest.mark.parametrize(
    ("status_code", "content", "json_error", "expected_message"),
    [
        (500, {"data": {"__typename": "Query"}}, False, "Unexpected status: 500"),
        (200, None, True, "Unexpected response body"),
        (200, {}, False, "Unexpected response: {}"),
        (
            200,
            {"data": {"__typename": "Product"}},
            False,
            "Unexpected response: {'data': {'__typename': 'Product'}}",
        ),
    ],
)
def test_check_response_rejects_invalid_response(
    status_code, content, json_error, expected_message
):
    # given
    response = Mock(status_code=status_code)
    if json_error:
        response.json.side_effect = requests.exceptions.JSONDecodeError(
            "Expecting value", "", 0
        )
    else:
        response.json.return_value = content

    # when/then
    with pytest.raises(AssertionError, match=re.escape(expected_message)):
        check_response(response)
