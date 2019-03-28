from celery import shared_task

from ..core.utils import create_thumbnails
from .models import User


@shared_task
def create_user_avatar_thumbnails(user_id):
    """Creates thumbnails for user avatar."""
    create_thumbnails(
        pk=user_id,
        model=User,
        size_set='user_avatars',
        image_attr='avatar',
    )
