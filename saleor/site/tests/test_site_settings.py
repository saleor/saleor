from django.contrib.sites.models import Site

from ..models import SiteSettings


def test_new_get_current():
    result = Site.objects.get_current()
    assert result.name == "mirumee.com"
    assert result.domain == "mirumee.com"
    assert type(result.settings) == SiteSettings
