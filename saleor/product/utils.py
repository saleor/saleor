from django.core.exceptions import ObjectDoesNotExist


def get_attributes_display(variant, attributes):
    display = {}
    for attribute in attributes:
        value = variant.get_attribute(attribute.pk)
        if value:
            try:
                choice = attribute.values.get(pk=value)
            except ObjectDoesNotExist:
                pass
            except ValueError:
                display[attribute.pk] = value
            else:
                display[attribute.pk] = choice.display
    return display
