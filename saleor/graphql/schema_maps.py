from typing import Dict, List

from graphene.types.definitions import GrapheneObjectType
from graphene.utils.str_converters import to_camel_case
from graphql.type.definition import GraphQLType

from .core.fields import CustomField

TypeMap = Dict[str, GraphQLType]
SensitiveFieldsMap = Dict[str, List[str]]


def _get_field_name(name: str, camelcase=True) -> str:
    if camelcase:
        return to_camel_case(name)
    return name


def build_sensitive_fields_map(type_map: TypeMap, camelcase=True) -> SensitiveFieldsMap:
    sensitive_fields: SensitiveFieldsMap = {}
    for type_name, gql_type in type_map.items():
        if isinstance(gql_type, GrapheneObjectType):
            for field_name, field in gql_type.graphene_type._meta.fields.items():
                if isinstance(field, CustomField) and field.sensitive:
                    field_name = field.name or _get_field_name(field_name, camelcase)
                    if field_name not in gql_type.fields:
                        continue
                    sensitive_fields.setdefault(type_name, []).append(field_name)
    return sensitive_fields
