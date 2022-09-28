from ...attribute import models
from ..account.dataloaders import load_requestor


def resolve_attributes(info, qs=None):
    requestor = load_requestor(info.context)
    qs = qs or models.Attribute.objects.get_visible_to_user(requestor)
    return qs.distinct()


def resolve_attribute_by_id(id):
    return models.Attribute.objects.filter(id=id).first()


def resolve_attribute_by_slug(slug):
    return models.Attribute.objects.filter(slug=slug).first()
