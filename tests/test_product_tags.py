from mock import Mock
from saleor.product.templatetags.product_images import get_thumbnail, product_first_image


def test_get_thumbnail():
    instance = Mock()
    cropped_value = Mock(url='crop.jpg')
    thumbnail_value = Mock(url='thumb.jpg')
    instance.crop = {'10x10': cropped_value}
    instance.thumbnail = {'10x10': thumbnail_value}
    cropped = get_thumbnail(instance, '10x10', method='crop')
    assert cropped == cropped_value.url
    thumb = get_thumbnail(instance, '10x10', method='thumbnail')
    assert thumb == thumbnail_value.url


def test_get_thumbnail_no_instance():
    output = get_thumbnail(instance=None, size='10x10', method='crop')
    assert output == '/static/images/product-image-placeholder.png'


def test_product_first_image():
    mock_product_image = Mock()
    mock_product_image.image = Mock()
    mock_product_image.image.crop = {'10x10': Mock(url='crop.jpg')}

    mock_queryset = Mock()
    mock_queryset.all.return_value = [mock_product_image]
    mock_product = Mock(images=mock_queryset)
    out = product_first_image(mock_product, '10x10', method='crop')
    assert out == 'crop.jpg'
