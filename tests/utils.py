from io import BytesIO
from typing import Dict, Set, Union
from urllib.parse import urlparse

from django.core.files.uploadedfile import SimpleUploadedFile
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
    image_name = image_name
    image = SimpleUploadedFile(image_name + ".jpg", img_data.getvalue(), "image/png")
    return image, image_name


def create_pdf_file_with_image_ext():
    file_name = "product.jpg"
    file_data = SimpleUploadedFile(file_name, b"product_data", "application/pdf")
    return file_data, file_name


def money(amount):
    return Money(amount, "USD")


def generate_attribute_map(obj: Union[Product, ProductVariant]) -> Dict[int, Set[int]]:
    """Generate a map from a product or variant instance, useful to quickly compare
    the assigned attribute values against expected IDs.

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
