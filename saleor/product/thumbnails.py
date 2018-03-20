from celery import shared_task
from ..core.utils import create_thumbnails
from .models import ProductImage


@shared_task
def create_product_thumbnails(product_image_id: int):
    create_thumbnails(pk=product_image_id, model=ProductImage,
                      size_set='products')
