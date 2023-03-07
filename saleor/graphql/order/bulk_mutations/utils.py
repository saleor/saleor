from typing import Any, Dict

from django.core.exceptions import ValidationError
from graphql.error import GraphQLError

from ...core.utils import from_global_id_or_error


def get_instance(
    input: Dict[str, Any],
    model,
    key_map: Dict[str, str],
    instance_storage: Dict[str, Any],
):
    """Resolve instance based on input data, model and `key_map` argument provided.

    Args:
        input: data from input
        model: database model associated with searched instance
        key_map: mapping between keys from input and keys from database
        instance_storage: dict with key pattern: {model_name}_{key_name}_{key_value}
                          and instances as values; it is used to search for already
                          resolved instances

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
    if sum((input.get(key) is not None for key in key_map.keys())) > 1:
        args = ", ".join((k for k in key_map.keys()))
        raise ValidationError(
            f"Only one of [{args}] arguments can be provided "
            f"to resolve {model_name} instance."
        )

    if all((input.get(key) is None for key in key_map.keys())):
        args = ", ".join((k for k in key_map.keys()))
        raise ValidationError(
            f"One of [{args}] arguments must be provided "
            f"to resolve {model_name} instance."
        )

    for data_key, db_key in key_map.items():
        if input.get(data_key) and isinstance(input.get(data_key), str):
            if db_key == "id":
                try:
                    _, id = from_global_id_or_error(
                        input.get(data_key), model_name, raise_error=True
                    )
                    input[data_key] = id
                except GraphQLError as err:
                    raise ValidationError(err.message)

            lookup_key = "_".join((model_name, db_key, input[data_key]))
            instance = instance_storage.get(lookup_key)
            if instance:
                return instance

            instance = model.objects.filter(**{db_key: input[data_key]}).first()
            if not instance:
                raise ValidationError(
                    f"{model_name} instance with {db_key}={input[data_key]} "
                    f"doesn't exist."
                )

            instance_storage[lookup_key] = instance
            return instance

    raise ValidationError(f"Can't return {model_name} instance.")
