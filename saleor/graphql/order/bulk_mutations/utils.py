from typing import Any

from django.core.exceptions import ValidationError
from graphql.error import GraphQLError

from ....order.error_codes import OrderBulkCreateErrorCode
from ...core.utils import from_global_id_or_error


def get_instance(
    input: dict[str, Any],
    model,
    key_map: dict[str, str],
    instance_storage: dict[str, Any],
    error_enum: type[OrderBulkCreateErrorCode],
    path: str = "",
):
    """Resolve instance based on input data, model and `key_map` argument provided.

    Args:
        input: data from input
        model: database model associated with searched instance
        key_map: mapping between keys from input and keys from database
        instance_storage: dict with key pattern: {model_name}_{key_name}_{key_value}
                          and instances as values; it is used to search for already
                          resolved instances
        error_enum: enum with error codes
        path: path to input field, which caused an error

    Return:
        Model instance

    Raise:
        ValidationError:
            - if multiple keys provided in input
            - if no key provided in input
            - if global id can't be resolved ( in case of `id` database key)
            - if instance can't be resolved by

    """
    model_name = model.__name__
    if len(key_map) > 1:
        if sum(input.get(key) is not None for key in key_map.keys()) > 1:
            args = ", ".join(k for k in key_map.keys())
            raise ValidationError(
                message=f"Only one of [{args}] arguments can be provided "
                f"to resolve {model_name} instance.",
                code=error_enum.TOO_MANY_IDENTIFIERS.value,
                params={"path": path},
            )

        if all(input.get(key) is None for key in key_map.keys()):
            args = ", ".join(k for k in key_map.keys())
            raise ValidationError(
                message=f"One of [{args}] arguments must be provided "
                f"to resolve {model_name} instance.",
                code=error_enum.REQUIRED.value,
                params={"path": path},
            )

    for data_key, db_key in key_map.items():
        if input.get(data_key) and isinstance(input.get(data_key), str):
            if db_key == "id":
                try:
                    _, id = from_global_id_or_error(
                        str(input.get(data_key)), model_name, raise_error=True
                    )
                    input[data_key] = id
                except GraphQLError as err:
                    raise ValidationError(
                        message=err.message,
                        code=error_enum.INVALID.value,
                        params={"path": f"{path}.{data_key}" if path else data_key},
                    )

            lookup_key = ".".join((model_name, db_key, input[data_key]))
            instance = instance_storage.get(lookup_key)
            if not instance:
                raise ValidationError(
                    message=f"{model_name} instance with {db_key}={input[data_key]} "
                    f"doesn't exist.",
                    code=error_enum.NOT_FOUND.value,
                    params={"path": f"{path}.{data_key}" if path else data_key},
                )
            return instance

    raise ValidationError(
        message=f"Can't return {model_name} instance.",
        code=error_enum.NOT_FOUND.value,
        params={"path": path},
    )
