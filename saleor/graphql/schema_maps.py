from typing import Dict, Set, Tuple

from graphene.types.definitions import GrapheneObjectType
from graphene.utils.str_converters import to_camel_case
from graphql.type.definition import GraphQLType

from .api import schema
from .core.fields import CostField, FieldCost

TypeMap = Dict[str, GraphQLType]
SensitiveFieldsMap = Dict[str, Set[str]]
FieldsCostMap = Dict[str, Dict[str, FieldCost]]


def _get_field_name(name: str, camelcase=True) -> str:
    if camelcase:
        return to_camel_case(name)
    return name


def generate_schema_maps(
    type_map: TypeMap, camelcase=True
) -> Tuple[SensitiveFieldsMap, FieldsCostMap]:
    sensitive_map: SensitiveFieldsMap = {}
    cost_map: FieldsCostMap = {}

    for type_name, gql_type in type_map.items():
        if not isinstance(gql_type, GrapheneObjectType):
            continue
        for field_name, field in gql_type.graphene_type._meta.fields.items():
            if not isinstance(field, CostField):
                continue
            field_name = field.name or _get_field_name(field_name, camelcase)
            if field_name not in gql_type.fields:
                continue
            if field.sensitive:
                sensitive_map.setdefault(type_name, set()).add(field_name)
            if field.cost is not None:
                cost_map.setdefault(type_name, {})[field_name] = field.cost
    return sensitive_map, cost_map


SENSITIVE_FIELDS_MAP, COST_MAP = generate_schema_maps(schema.get_type_map())
