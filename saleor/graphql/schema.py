import re
from copy import copy

from graphene.utils.str_converters import to_camel_case
from graphene_directives import schema
from graphene_directives.directive import CustomDirectiveMeta
from graphene_directives.exceptions import (
    DirectiveCustomValidationError,
    DirectiveValidationError,
)
from graphene_directives.parsers import (
    arg_camel_case,
    arg_snake_case,
    decorator_string,
    entity_type_to_fields_string,
    enum_type_to_fields_string,
    input_type_to_fields_string,
)
from graphene_directives.utils import get_field_attribute_value, has_field_attribute
from graphene_federation.schema import Schema as FederationSchema
from graphql import (
    DirectiveLocation,
    GraphQLArgument,
    GraphQLEnumType,
    GraphQLField,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLObjectType,
    is_enum_type,
    is_input_type,
    is_interface_type,
    is_object_type,
)
from graphql.utilities.print_schema import (
    print_args,
    print_description,
    print_input_value,
)


def patch_federation_schema():
    # https://github.com/strollby/graphene-directives/issues/14

    def get_single_field_type(
        entity: GraphQLEnumType | GraphQLInputObjectType | GraphQLObjectType,
        field_name: str,
        field_type: GraphQLInputField | GraphQLField,
        is_enum_type: bool = False,
    ) -> GraphQLEnumType | GraphQLInputObjectType | GraphQLObjectType:
        new_entity = copy(entity)
        setattr(
            new_entity, "values" if is_enum_type else "fields", {field_name: field_type}
        )
        return new_entity

    schema.get_single_field_type = get_single_field_type

    # https://github.com/strollby/graphene-directives/issues/15

    def _add_argument_decorators(
        self,
        entity_name: str,
        required_directive_field_types: set[DirectiveLocation],
        args: dict[str, GraphQLArgument],
        original_args: dict[str, GraphQLArgument],
    ) -> str:
        """For a given field, go through all its args and see if any directive decorator needs to be added."""

        if not args:
            return ""

        # If every arg does not have a description, print them on one line.
        print_single_line = not any(arg.description for arg in args.values())
        indentation: str = "  "
        new_args = []

        str_field = "(" if print_single_line else "(\n"

        for i, (name, arg) in enumerate(args.items()):
            original_arg_name = to_camel_case(name)
            original_arg = original_args[original_arg_name]
            name = self.type_attribute_to_field_name(name)
            if print_single_line:
                base_str = f"{print_input_value(name, original_arg)} "
            else:
                base_str = (
                    print_description(arg, f"  {indentation}", not i)
                    + f"  {indentation}"
                    + f"{print_input_value(name, original_arg)} "
                )
            directives = []
            for directive in self.custom_directives:
                if has_field_attribute(arg, directive):
                    directive_values = get_field_attribute_value(arg, directive)
                    meta_data: CustomDirectiveMeta = getattr(
                        directive, "_graphene_directive"
                    )

                    if (
                        not required_directive_field_types.intersection(
                            set(directive.locations)
                        )
                        and len(required_directive_field_types) != 0
                    ):
                        raise DirectiveValidationError(
                            "\n".join(
                                [
                                    f"{str(directive)} cannot be used at argument {name} level",
                                    f"\tat {entity_name}",
                                    f"\tallowed: {directive.locations}",
                                    f"\trequired: {required_directive_field_types}",
                                ]
                            )
                        )

                    for directive_value in directive_values:
                        if meta_data.input_transform is not None:
                            directive_value = arg_camel_case(
                                meta_data.input_transform(
                                    arg_snake_case(directive_value), self
                                )
                            )

                        directive_str = decorator_string(directive, **directive_value)
                        directives.append(directive_str)

            new_args.append(base_str + " ".join(directives))

        if print_single_line:
            str_field += ", ".join(new_args) + ")"
        else:
            str_field += "\n".join(new_args) + f"\n{indentation})"

        return str_field

    def _add_field_decorators(self, graphene_types: set, string_schema: str) -> str:
        """For a given entity, go through all its fields and see if any directive decorator needs to be added.

        This method simply goes through the fields that need to be modified and replace them with their annotated
        version in the schema string representation.
        """

        for graphene_type in graphene_types:
            entity_name = graphene_type._meta.name  # noqa

            entity_type = self.graphql_schema.get_type(entity_name)
            get_field_graphene_type = self.field_name_to_type_attribute(graphene_type)

            required_directive_locations = set()

            if is_object_type(entity_type) or is_interface_type(entity_type):
                required_directive_locations.union(
                    {
                        DirectiveLocation.FIELD_DEFINITION,
                        DirectiveLocation.ARGUMENT_DEFINITION,
                    }
                )
            elif is_enum_type(entity_type):
                required_directive_locations.add(DirectiveLocation.ENUM_VALUE)
            elif is_input_type(entity_type):
                required_directive_locations.add(
                    DirectiveLocation.INPUT_FIELD_DEFINITION
                )
            else:
                continue

            if is_enum_type(entity_type):
                fields: dict = entity_type.values
            else:
                fields: dict = entity_type.fields

            str_fields = []

            for field_name, field in fields.items():
                if is_enum_type(entity_type):
                    str_field = enum_type_to_fields_string(
                        get_single_field_type(
                            entity_type, field_name, field, is_enum_type=True
                        )
                    )
                elif isinstance(field, GraphQLInputField):
                    str_field = input_type_to_fields_string(
                        get_single_field_type(entity_type, field_name, field)
                    )
                elif isinstance(field, GraphQLField):
                    str_field = entity_type_to_fields_string(
                        get_single_field_type(entity_type, field_name, field)
                    )

                    # Replace Arguments with directives
                    if hasattr(entity_type, "_fields"):
                        _arg = entity_type._fields.args[0]  # noqa
                        if hasattr(_arg, self.type_attribute_to_field_name(field_name)):
                            arg_field = getattr(
                                _arg, self.type_attribute_to_field_name(field_name)
                            )
                        else:
                            arg_field = {}

                        if (
                            hasattr(arg_field, "args")
                            and arg_field.args is not None
                            and isinstance(arg_field.args, dict)
                        ):
                            original_args = print_args(
                                args=field.args, indentation="  "
                            )
                            replacement_args = self._add_argument_decorators(
                                entity_name=entity_name,
                                required_directive_field_types=required_directive_locations,
                                args=arg_field.args,
                                original_args=field.args,
                            )
                            str_field = str_field.replace(
                                original_args, replacement_args
                            )
                else:
                    continue

                # Check if we need to annotate the field by checking if it has the decorator attribute set on the field.
                field = getattr(
                    graphene_type, get_field_graphene_type(field_name), None
                )
                if field is None:
                    # Append the string, but skip the directives
                    str_fields.append(str_field)
                    continue

                for directive in self.custom_directives:
                    if not has_field_attribute(field, directive):
                        continue
                    directive_values = get_field_attribute_value(field, directive)

                    meta_data: CustomDirectiveMeta = getattr(
                        directive, "_graphene_directive"
                    )

                    if (
                        not required_directive_locations.intersection(
                            set(directive.locations)
                        )
                        and len(required_directive_locations) != 0
                    ):
                        raise DirectiveValidationError(
                            "\n".join(
                                [
                                    f"{str(directive)} cannot be used at field level",
                                    f"\tat {entity_name}",
                                    f"\tallowed: {directive.locations}",
                                    f"\trequired: {required_directive_locations}",
                                ]
                            )
                        )

                    for directive_value in directive_values:
                        if (
                            meta_data.field_validator is not None
                            and not meta_data.field_validator(
                                entity_type,
                                field,
                                arg_snake_case(directive_value),
                                self,
                            )
                        ):
                            raise DirectiveCustomValidationError(
                                ", ".join(
                                    [
                                        f"Custom Validation Failed for {str(directive)} with args: ({directive_value})"
                                        f"at field level {entity_name}:{field}"
                                    ]
                                )
                            )

                        if meta_data.input_transform is not None:
                            directive_value = arg_camel_case(
                                meta_data.input_transform(
                                    arg_snake_case(directive_value), self
                                )
                            )

                        str_field += (
                            f" {decorator_string(directive, **directive_value)}"
                        )

                str_fields.append(str_field)

            str_fields_annotated = "\n".join(str_fields)

            # Replace the original field declaration by the annotated one
            if is_object_type(entity_type):
                entity_type_name = "type"
                str_fields_original = entity_type_to_fields_string(entity_type)
            elif is_interface_type(entity_type):
                entity_type_name = "interface"
                str_fields_original = entity_type_to_fields_string(entity_type)
            elif is_enum_type(entity_type):
                entity_type_name = "enum"
                str_fields_original = enum_type_to_fields_string(entity_type)
            elif is_input_type(entity_type):
                entity_type_name = "input"
                str_fields_original = input_type_to_fields_string(entity_type)
            else:
                continue

            pattern = re.compile(
                r"(%s\s%s\s[^\{]*)\{\s*%s\s*\}"  # noqa
                % (entity_type_name, entity_name, re.escape(str_fields_original))
            )

            # Escape backslashes to ensure that `\\n` is not replaced with a newline character
            # see: https://github.com/strollby/graphene-directives/pull/10
            escaped_str_fields_annotated = str_fields_annotated.replace("\\", "\\\\")
            string_schema = pattern.sub(
                rf"\g<1> {{\n{escaped_str_fields_annotated}\n}}", string_schema
            )
        return string_schema

    FederationSchema._add_argument_decorators = _add_argument_decorators
    FederationSchema._add_field_decorators = _add_field_decorators
