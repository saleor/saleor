def get_attributes_display_map(variant, attributes):
    display = {}
    for attribute in attributes:
        value = variant.get_attribute(attribute.pk)
        if value:
            choices = attribute.values.all()
            if choices:
                for choice in attribute.values.all():
                    if choice.pk == value:
                        display[attribute.pk] = choice
                        break
            else:
                display[attribute.pk] = value
    return display
