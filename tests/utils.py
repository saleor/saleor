from io import BytesIO
from urllib.parse import urlparse

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q
from django.utils.encoding import smart_text
from PIL import Image
from prices import Money


def get_url_path(url):
    parsed_url = urlparse(url)
    return parsed_url.path


def get_redirect_location(response):
    # Due to Django 1.8 compatibility, we have to handle both cases
    return get_url_path(response['Location'])


def filter_products_by_attribute(queryset, attribute_id, value):
    key = smart_text(attribute_id)
    value = smart_text(value)
    in_product = Q(attributes__contains={key: value})
    in_variant = Q(variants__attributes__contains={key: value})
    return queryset.filter(in_product | in_variant)


def get_form_errors(response, form_name='form'):
    errors = response.context.get(form_name).errors
    return errors.get('__all__') if errors else []


def compare_taxes(taxes_1, taxes_2):
    assert len(taxes_1) == len(taxes_2)

    for rate_name, tax in taxes_1.items():
        value_1 = tax['value']
        value_2 = taxes_2.get(rate_name)['value']
        assert value_1 == value_2


def create_image(image_name='product2'):
    img_data = BytesIO()
    image = Image.new('RGB', size=(1, 1), color=(255, 0, 0, 0))
    image.save(img_data, format='JPEG')
    image_name = image_name
    image = SimpleUploadedFile(
        image_name + '.jpg', img_data.getvalue(), 'image/png')
    return image, image_name


def create_pdf_file_with_image_ext():
    file_name = 'product.jpg'
    file_data = SimpleUploadedFile(
        file_name, b'product_data', 'application/pdf')
    return file_data, file_name


def money(amount):
    return Money(amount, 'USD')
