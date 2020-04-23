import graphene

from ...page import models


def resolve_page(info, global_page_id=None, slug=None):
    assert global_page_id or slug, "No page ID or slug provided."
    user = info.context.user

    if slug is not None:
        page = models.Page.objects.visible_to_user(user).filter(slug=slug).first()
    else:
        _type, page_pk = graphene.Node.from_global_id(global_page_id)
        page = models.Page.objects.visible_to_user(user).filter(pk=page_pk).first()
    return page


def resolve_pages(info, **_kwargs):
    user = info.context.user
    return models.Page.objects.visible_to_user(user)
