from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from promise import Promise

from ....attribute.models import Attribute, AttributeValue
from ...core.context import SaleorContext
from .attributes import AttributesByAttributeId, AttributeValueByIdLoader


@dataclass(frozen=True)
class CustomerAttributeConditionData:
    """A condition on one customer attribute: the buyer must hold one of the values."""

    attribute: Attribute
    values: list[AttributeValue]


def load_customer_attribute_conditions(
    context: SaleorContext, value_ids: Iterable[int]
) -> Promise[list[CustomerAttributeConditionData]]:
    """Group the given attribute values by their attribute.

    Groups are ordered by attribute id and the values of a group by value id,
    so the result is stable for a given set of value ids.
    """

    def with_attributes(
        attributes: list[Attribute],
        values_by_attribute_id: dict[int, list[AttributeValue]],
    ) -> list[CustomerAttributeConditionData]:
        return [
            CustomerAttributeConditionData(
                attribute=attribute,
                values=sorted(
                    values_by_attribute_id[attribute.pk], key=lambda value: value.pk
                ),
            )
            for attribute in attributes
        ]

    def with_values(values: list[AttributeValue]):
        values_by_attribute_id: dict[int, list[AttributeValue]] = defaultdict(list)
        for value in values:
            values_by_attribute_id[value.attribute_id].append(value)
        attribute_ids = sorted(values_by_attribute_id)
        return (
            AttributesByAttributeId(context)
            .load_many(attribute_ids)
            .then(
                lambda attributes: with_attributes(attributes, values_by_attribute_id)
            )
        )

    return (
        AttributeValueByIdLoader(context).load_many(list(value_ids)).then(with_values)
    )
