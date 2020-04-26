from io import BytesIO
from typing import Dict, Set, Union
from urllib.parse import urlparse

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connections, transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce
from PIL import Image
from prices import Money

from saleor.product.models import Product, ProductVariant


def get_url_path(url):
    parsed_url = urlparse(url)
    return parsed_url.path


def get_redirect_location(response):
    # Due to Django 1.8 compatibility, we have to handle both cases
    return get_url_path(response["Location"])


def get_form_errors(response, form_name="form"):
    errors = response.context.get(form_name).errors
    return errors.get("__all__") if errors else []


def create_image(image_name="product2"):
    img_data = BytesIO()
    image = Image.new("RGB", size=(1, 1), color=(255, 0, 0, 0))
    image.save(img_data, format="JPEG")
    image = SimpleUploadedFile(image_name + ".jpg", img_data.getvalue(), "image/png")
    return image, image_name


def create_pdf_file_with_image_ext():
    file_name = "product.jpg"
    file_data = SimpleUploadedFile(file_name, b"product_data", "application/pdf")
    return file_data, file_name


def money(amount):
    return Money(amount, "USD")


def generate_attribute_map(obj: Union[Product, ProductVariant]) -> Dict[int, Set[int]]:
    """Generate a map from a product or variant instance.

    Useful to quickly compare the assigned attribute values against expected IDs.

    The below association map will be returned.

        {
            attribute_pk (int) => {attribute_value_pk (int), ...}
            ...
        }
    """

    qs = obj.attributes.select_related("assignment__attribute")
    qs = qs.prefetch_related("values")

    return {
        assignment.attribute.pk: {value.pk for value in assignment.values.all()}
        for assignment in qs
    }


def flush_post_commit_hooks():
    """Run all pending `transaction.on_commit()` callbacks.

    Forces all `on_commit()` hooks to run even if the transaction was not committed yet.
    """
    for alias in connections:
        connection = transaction.get_connection(alias)
        was_atomic = connection.in_atomic_block
        connection.in_atomic_block = False
        connection.run_and_clear_commit_hooks()
        connection.in_atomic_block = was_atomic


def get_quantity_allocated_for_stock(stock):
    """Count how many items are allocated for stock."""
    return stock.allocations.aggregate(
        quantity_allocated=Coalesce(Sum("quantity_allocated"), 0)
    )["quantity_allocated"]


def get_available_quantity_for_stock(stock):
    """Count how many stock items are available."""
    quantity_allocated = get_quantity_allocated_for_stock(stock)
    return max(stock.quantity - quantity_allocated, 0)
