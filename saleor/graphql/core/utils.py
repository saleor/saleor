import importlib
from typing import Callable

import graphene
from django.core.exceptions import ValidationError


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


def lazy_resolve(name) -> Callable:
    """Lazy import a graphql object when facing circular imports issues.

    >>> # Request the saleor.graphql.order.types.OrderLine object
    >>> OrderLine = lazy_resolve('order.types:OrderLine')()"""

    import_name, object_name = name.split(":")

    def _lazy_resolve():
        imported_module = importlib.import_module(f"...{import_name}", package=__name__)
        return getattr(imported_module, object_name)

    return _lazy_resolve
