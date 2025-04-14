def get_editable_values_from_instance(instance):
    field_names = [
        field.name for field in instance._meta.model._meta.fields if field.editable
    ]
    instance_values = {
        field_name: getattr(instance, field_name) for field_name in field_names
    }
    return instance_values


def get_edited_fields(old_values: dict, new_values: dict):
    return [
        field
        for field in old_values.keys()
        if old_values.get(field) != new_values.get(field)
    ]
