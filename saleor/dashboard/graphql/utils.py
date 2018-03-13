import graphene


def get_model_name(model):
    model_name = model.__name__
    return model_name[:1].lower() + model_name[1:]


def get_model_type_and_fields(registry, model, return_field_name):
    model_type = registry.get_type_for_model(model)
    # get mutation output field for model instance
    fields = {return_field_name: graphene.Field(model_type)}
    return model_type, fields
