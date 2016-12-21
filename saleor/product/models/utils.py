from django.utils.encoding import smart_text


def get_attributes_display_map(obj, attributes):
    display = {}
    for attribute in attributes:
        value = obj.attributes.get(smart_text(attribute.pk))
        if value:
            choices = {smart_text(a.pk): a for a in attribute.values.all()}
            attr = choices.get(value)
            if attr:
                display[attribute.pk] = attr
            else:
                display[attribute.pk] = value
    return display
