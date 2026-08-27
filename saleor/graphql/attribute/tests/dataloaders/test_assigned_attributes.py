from ....context import SaleorContext
from ...dataloaders.assigned_attributes import (
    AttributeValuesByProductIdAndAttributeIdAndLimitLoader,
)
from ...dataloaders.attributes import AttributeValueByIdLoader


def test_attribute_values_loader_with_value_missing_from_database(product, monkeypatch):
    """A value the loader cannot find (e.g. replica lag) is skipped, not a crash."""
    # given
    attribute = product.product_type.product_attributes.first()
    context = SaleorContext()
    monkeypatch.setattr(
        AttributeValueByIdLoader,
        "batch_load",
        lambda self, keys: [None] * len(keys),
    )

    # when
    values = (
        AttributeValuesByProductIdAndAttributeIdAndLimitLoader(context)
        .batch_load([(product.pk, attribute.pk, None)])
        .get()
    )

    # then
    assert values == [[]]
