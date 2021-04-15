from typing import TYPE_CHECKING, Dict, Iterable, List, Union

from django.db import transaction
from ..models import Post


if TYPE_CHECKING:
    # flake8: noqa
    from datetime import date, datetime
    from django.db.models.query import QuerySet
    from ..models import Post


@transaction.atomic
def delete_posts(posts_ids: List[str]):
    """Delete posts and perform all necessary actions.

    Set products of deleted posts as unpublished.
    """
    posts = Post.objects.select_for_update().filter(pk__in=posts_ids)
    posts.delete()