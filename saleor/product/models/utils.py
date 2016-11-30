def get_attributes_display_map(variant, attributes):
    display_map = {}
    for attribute in attributes:
        value_pk = variant.get_attribute(attribute.pk)
        if value_pk:
            value_pk = int(value_pk)
            choices = {a.pk: a for a in attribute.values.all()}
            choice_obj = choices.get(value_pk)
            if choice_obj:
                display_map[attribute.pk] = choice_obj
            else:
                display_map[attribute.pk] = value
    return display_map
