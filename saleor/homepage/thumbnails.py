from celery import shared_task

from ..core.utils import create_thumbnails
from .models import HomePageItem


@shared_task
def create_product_thumbnails(homepage_block_id):
    """Takes ProductImage model, and creates thumbnails for it."""
    create_thumbnails(
        pk=homepage_block_id, model=HomePageItem, image_attr='cover',
        size_set='homepage-block')
