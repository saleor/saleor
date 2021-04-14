import graphene

from ...store import models
from ..core.validators import validate_one_of_args_is_in_query
from .types import Store, StoreType


def resolve_store(info, global_page_id=None, slug=None):
    validate_one_of_args_is_in_query("id", global_page_id, "slug", slug)
    user = info.context.user

    if slug is not None:
        store = models.Store.objects.visible_to_user(user).filter(slug=slug).first()
    else:
        _type, store_pk = graphene.Node.from_global_id(global_page_id)
        store = models.Store.objects.visible_to_user(user).filter(pk=store_pk).first()
    return store


def resolve_stores(info, **_kwargs):
    return models.Store.objects.all()


def resolve_store_type(info, global_store_type_id):
    return graphene.Node.get_node_from_global_id(info, global_store_type_id, StoreType)


def resolve_store_types(info, **_kwargs):
    return models.StoreType.objects.all()
