import pytest
from django.conf import settings

from ..notification.utils import LOGO_URL
from ..utils import queryset_in_batches


def get_site_context_payload(site):
    domain = site.domain
    return {
        "site_name": site.name,
        "domain": domain,
        "logo_url": f"http://{domain}{settings.STATIC_URL}{LOGO_URL}",
    }


@pytest.mark.parametrize(
    ("batch_size", "batch_count"),
    [(1, 5), (2, 3), (3, 2), (4, 2), (5, 1), (6, 1), (100, 1), (0, 0), (-1, 0)],
)
def test_queryset_in_batches(batch_size, batch_count, voucher_with_many_codes):
    # given
    codes = voucher_with_many_codes.codes.all()

    # when
    batches = [pks for pks in queryset_in_batches(codes, batch_size=batch_size)]
    pks = set([pk for pks in batches for pk in pks])

    # then
    assert len(batches) == batch_count
    if batch_size > 0:
        assert len(pks) == 5
