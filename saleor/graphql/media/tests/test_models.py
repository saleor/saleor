import pytest
from django.db.utils import IntegrityError

from ....product import MediaOwnerTypes
from ....product.models import ProductMedia


@pytest.mark.parametrize("owner_type", MediaOwnerTypes.ALL)
def test_owner_deletion_cascades_to_media(owner_type, media_owner):
    # given
    media = media_owner.media.create(alt="alt")
    assert ProductMedia.objects.filter(pk=media.pk).exists() is True

    # when
    media_owner.delete()

    # then
    assert ProductMedia.objects.filter(pk=media.pk).exists() is False


def test_media_cannot_have_two_owners(product, page):
    # when / then
    with pytest.raises(IntegrityError):
        ProductMedia.objects.create(product=product, page=page, alt="alt")


@pytest.mark.parametrize("owner_type", MediaOwnerTypes.ALL)
def test_owner_type_and_owner_resolve_from_the_set_foreign_key(owner_type, media_owner):
    # given
    media = media_owner.media.create(alt="alt")

    # when / then
    assert media.owner_type == owner_type
    assert media.owner == media_owner


def test_owner_less_media_has_no_owner():
    # given
    media = ProductMedia(alt="alt")

    # when / then
    assert media.owner_type is None
    assert media.owner is None
    assert media.get_ordering_queryset().exists() is False


@pytest.mark.parametrize("owner_type", MediaOwnerTypes.ALL)
def test_sort_order_is_assigned_per_owner(owner_type, media_owner):
    # given / when
    first = media_owner.media.create(alt="first")
    second = media_owner.media.create(alt="second")

    # then
    assert first.sort_order == 0
    assert second.sort_order == 1
