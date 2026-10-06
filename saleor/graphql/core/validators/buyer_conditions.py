from collections.abc import Iterable

import graphene
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from ....account.models import CustomerType
from ....attribute.models import AttributeValue
from ....product.utils.scoped_price_rows import get_ineligible_attribute_value_ids
from ...utils import get_nodes

MAX_CONDITIONS_PER_DIMENSION = 100

GRAPHQL_ERROR_CODE = "graphql_error"


def clean_customer_type_ids(
    items: Iterable[str | CustomerType] | None, invalid_code: str
) -> frozenset[int]:
    """Resolve customer types given as global ids or as already loaded nodes.

    An empty or missing list means no condition. Raises a `ValidationError`
    with `invalid_code` when the list is too long, and with the GraphQL error
    code when an id does not resolve to a customer type.
    """
    items = list(items or [])
    if not items:
        return frozenset()
    _validate_list_size(items, invalid_code)
    customer_types = _get_nodes(items, "CustomerType", CustomerType)
    return frozenset(customer_type.pk for customer_type in customer_types)


def clean_attribute_value_ids(
    items: Iterable[str | AttributeValue] | None,
    invalid_code: str,
    *,
    purpose: str,
    params_field: str = "attribute_values",
) -> frozenset[int]:
    """Resolve attribute values given as global ids or as already loaded nodes.

    Only values of customer attributes with a fixed set of choices can be a
    buyer condition. The ineligible ones are reported through `params_field`
    and `purpose` completes the message, such as "scope a price".
    """
    items = list(items or [])
    if not items:
        return frozenset()
    _validate_list_size(items, invalid_code)
    values = _get_nodes(items, "AttributeValue", AttributeValue)
    value_ids = frozenset(value.pk for value in values)
    if ineligible_ids := get_ineligible_attribute_value_ids(value_ids):
        raise ValidationError(
            "Only values of customer attributes with a fixed set of choices can "
            f"{purpose}.",
            code=invalid_code,
            params={
                params_field: [
                    graphene.Node.to_global_id("AttributeValue", value_id)
                    for value_id in sorted(ineligible_ids)
                ]
            },
        )
    return value_ids


def _validate_list_size(items: list, invalid_code: str) -> None:
    if len(items) > MAX_CONDITIONS_PER_DIMENSION:
        raise ValidationError(
            f"Provide at most {MAX_CONDITIONS_PER_DIMENSION} items.",
            code=invalid_code,
        )


def _get_nodes(items: list, type_name: str, model) -> list:
    """Return the nodes, resolving global ids and checking loaded nodes' type.

    A mutation may have resolved the ids into nodes of whatever type the ids
    encoded, so loaded nodes are checked against the expected model.
    """
    ids = [item for item in items if isinstance(item, str)]
    nodes = [item for item in items if not isinstance(item, str)]
    if wrong_nodes := [node for node in nodes if not isinstance(node, model)]:
        wrong_ids = [
            graphene.Node.to_global_id(type(node).__name__, node.pk)
            for node in wrong_nodes
        ]
        raise ValidationError(
            f"Must receive {type_name} ids, got: {wrong_ids}.",
            code=GRAPHQL_ERROR_CODE,
        )
    if ids:
        try:
            nodes.extend(get_nodes(ids, type_name, model=model))
        except GraphQLError as error:
            raise ValidationError(str(error), code=GRAPHQL_ERROR_CODE) from error
    return nodes
