def clean_seo_fields(data):
    """Extract and assign seo fields to given dictionary."""
    seo_fields = data.pop('seo', None)
    if seo_fields:
        data['seo_title'] = seo_fields.get('title')
        data['seo_description'] = seo_fields.get('description')
