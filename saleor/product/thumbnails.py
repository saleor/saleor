from ..celeryconf import app
from ..core.utils import create_thumbnails
from .models import ProductMedia


@app.task
def create_product_thumbnails(image_id: str):
    """Take a ProductMedia model and create thumbnails for it."""
    create_thumbnails(pk=image_id, model=ProductMedia, size_set="products")
