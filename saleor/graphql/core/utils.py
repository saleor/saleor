def clean_seo_fields(data):
    """Extract and assign seo fields to given dictionary."""
    seo_fields = data.pop('seo', None)
    if seo_fields:
        data['seo_title'] = seo_fields.get('title')
        data['seo_description'] = seo_fields.get('description')


def snake_to_camel_case(name):
    """Convert snake_case variable name to camelCase."""
    if isinstance(name, str):
        splitted = name.split('_')
        return splitted[0] + "".join(map(str.capitalize, splitted[1:]))
    return name
