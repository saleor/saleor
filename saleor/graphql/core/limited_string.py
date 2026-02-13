import graphene


def LimitedString(*, min_length=None, max_length=None, **kwargs):
    if min_length is not None:
        assert min_length >= 1, "min_length must be >= 1"
    if max_length is not None:
        assert max_length >= 1, "max_length must be >= 1"
    if min_length is not None and max_length is not None:
        assert min_length <= max_length, "min_length must be <= max_length"

    # Auto-compute description suffix
    parts = []
    if min_length is not None:
        parts.append(f"Minimum {min_length}")
    if max_length is not None:
        parts.append(f"maximum {max_length}")

    if parts:
        constraint_suffix = " (" + ", ".join(parts) + " characters.)"
        description = kwargs.get("description", "")
        kwargs["description"] = description + constraint_suffix

    field = graphene.String(**kwargs)
    field._limited_min_length = min_length
    field._limited_max_length = max_length
    return field
