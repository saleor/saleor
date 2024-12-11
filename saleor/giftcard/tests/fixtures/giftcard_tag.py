import pytest

from ...models import GiftCardTag


@pytest.fixture
def gift_card_tag_list(db):
    tags = [GiftCardTag(name=f"test-tag-{i}") for i in range(5)]
    return GiftCardTag.objects.bulk_create(tags)
