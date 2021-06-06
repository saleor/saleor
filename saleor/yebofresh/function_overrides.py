from django.utils.text import slugify as original_slugify


def slugify(value, allow_unicode):
    """
    We want to allow decimal point values in attribute values, this
    override allows us to do so by replacing "." with "_" in the
    slug, rather than just throwing away "." and hitting issues
    with non-uniqueness.
    For instance if you don't use this function and try to pass
    values "1.8" and "18", it will try to create two "18" slugs
    which will raise an error.
    Instead, now the first slug will be "1_8".
    """
    val = value.replace(".", "_")
    return original_slugify(val, allow_unicode=allow_unicode)
