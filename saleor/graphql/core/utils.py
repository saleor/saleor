from typing import List

import graphene
import graphene_django_optimizer as gql_optimizer
from django.core.exceptions import ValidationError

from .interfaces import MoveOperation


def clean_seo_fields(data):
    """Extract and assign seo fields to given dictionary."""
    seo_fields = data.pop("seo", None)
    if seo_fields:
        data["seo_title"] = seo_fields.get("title")
        data["seo_description"] = seo_fields.get("description")


def snake_to_camel_case(name):
    """Convert snake_case variable name to camelCase."""
    if isinstance(name, str):
        split_name = name.split("_")
        return split_name[0] + "".join(map(str.capitalize, split_name[1:]))
    return name


def str_to_enum(name):
    """Create an enum value from a string."""
    return name.replace(" ", "_").replace("-", "_").upper()


def validate_image_file(file, field_name):
    """Validate if the file is an image."""
    if not file.content_type.startswith("image/"):
        raise ValidationError({field_name: "Invalid file type"})


def from_global_id_strict_type(info, global_id, only_type, field="id"):
    """Resolve a node global id with a strict given type required."""
    _type, _id = graphene.Node.from_global_id(global_id)
    graphene_type = info.schema.get_type(_type).graphene_type
    if graphene_type != only_type:
        raise ValidationError({field: "Couldn't resolve to a node: %s" % global_id})
    return _id


def get_node_optimized(qs, lookup, info):
    qs = qs.filter(**lookup)
    qs = gql_optimizer.query(qs, info)
    return qs[0] if qs else None


def _prepare_reordering_operations(moves: List[MoveOperation]):
    """Updates the 'moves' relative sort orders to an absolute sorting."""

    current_rel_pos = None

    for move in moves:
        node = move.node

        if current_rel_pos is None:
            # This case happens when products created using a bulk_creation
            # e.g., bulk_create or collections.add
            if node.sort_order is None:
                current_rel_pos = (
                    node.get_max_sort_order(node.get_ordering_queryset()) or 0
                )
            else:
                current_rel_pos = node.sort_order
        else:
            current_rel_pos += 1

        new_position = max(0, current_rel_pos + move.sort_order)
        move.sort_order = new_position


def perform_reordering(moves: List[MoveOperation], field: str = "sort_order"):
    """This utility takes a set of operations containing a node
    and a relative sort order. It then converts the relative sorting
    to an absolute sorting.

    This will then commit the changes onto the nodes.

    Example usage:
    >>> from typing import Dict, Tuple
    >>>
    >>> from graphene import Node
    >>>
    >>> from saleor.graphql.core.interfaces import MoveOperation
    >>>
    >>>
    >>> # operations => [(node_id, relative_sort_order), ...]
    >>>
    >>> def reorder_my_models(info, operations: List[Tuple[int, int]]):
    ...
    ...     # moves => [OP(node, sort_order), ...]
    ...     moves = [
    ...         MoveOperation(Node.from_global_id(node=op[0]), sort_order=op[1])
    ...         for op in operations
    ...     ]
    ...
    ...     perform_reordering(moves)
    ...
    """
    _prepare_reordering_operations(moves)

    for move in moves:
        move.node.sort_order = move.sort_order
        move.node.save(update_fields=[field])
