import pytest
from django.db.utils import IntegrityError

from ....media import MediaOwnerTypes
from ....media.utils import OWNER_TYPE_TO_MEDIA_MODEL
from ....product.models import ProductMedia


@pytest.mark.parametrize("owner_type", MediaOwnerTypes.ALL)
def test_owner_deletion_cascades_to_media(owner_type, media_owner):
    # given
    media_model = OWNER_TYPE_TO_MEDIA_MODEL[owner_type]
    media = media_owner.media.create(alt="alt")
    assert media_model.objects.filter(pk=media.pk).exists() is True

    # when
    media_owner.delete()

    # then
    assert media_model.objects.filter(pk=media.pk).exists() is False


@pytest.mark.parametrize(
    "owner_type",
    [owner for owner in MediaOwnerTypes.ALL if owner != MediaOwnerTypes.PRODUCT],
)
def test_media_requires_an_owner(owner_type):
    # given
    media_model = OWNER_TYPE_TO_MEDIA_MODEL[owner_type]

    # when / then
    with pytest.raises(IntegrityError):
        media_model.objects.create(alt="alt")


@pytest.mark.parametrize("owner_type", MediaOwnerTypes.ALL)
def test_owner_type_and_owner_resolve_from_the_media_model(owner_type, media_owner):
    # given
    media = media_owner.media.create(alt="alt")

    # when / then
    assert media.owner_type == owner_type
    assert media.owner == media_owner
    assert media.owner_pk == media_owner.pk


def test_legacy_product_media_without_a_product_has_no_owner():
    """`ProductMedia.product` stays nullable, unlike every other media model."""
    # given
    media = ProductMedia(alt="alt")

    # when / then
    assert media.owner_type == MediaOwnerTypes.PRODUCT
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
