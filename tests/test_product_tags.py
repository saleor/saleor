from unittest.mock import Mock

from django.contrib.staticfiles.templatetags.staticfiles import static

from saleor.product.templatetags.product_images import (
    choose_placeholder, get_thumbnail, product_first_image)


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


def test_get_thumbnail_no_instance(monkeypatch):
    monkeypatch.setattr(
        'saleor.product.templatetags.product_images.choose_placeholder',
        lambda x: 'placeholder')
    output = get_thumbnail(instance=None, size='10x10', method='crop')
    assert output == static('placeholder')


def test_product_first_image():
    mock_product_image = Mock()
    mock_product_image.image = Mock()
    mock_product_image.image.crop = {'10x10': Mock(url='crop.jpg')}

    mock_queryset = Mock()
    mock_queryset.all.return_value = [mock_product_image]
    mock_product = Mock(images=mock_queryset)
    out = product_first_image(mock_product, '10x10', method='crop')
    assert out == 'crop.jpg'


def test_choose_placeholder(settings):
    settings.PLACEHOLDER_IMAGES = {
        10: '10_placeholder',
        20: '20_placeholder',
        30: '30_placeholder'}

    settings.DEFAULT_PLACEHOLDER = 'default_placeholder'

    # wrong or no size returns default
    assert choose_placeholder('wrong') == settings.DEFAULT_PLACEHOLDER
    assert choose_placeholder() == settings.DEFAULT_PLACEHOLDER

    # exact size
    assert choose_placeholder('10x10') == settings.PLACEHOLDER_IMAGES[10]

    # when exact not found, choose bigger available
    assert choose_placeholder('15x15') == settings.PLACEHOLDER_IMAGES[20]

    # like previous, but only one side bigger
    assert choose_placeholder('10x15') == settings.PLACEHOLDER_IMAGES[20]

    # when too big requested, choose the biggest available
    assert choose_placeholder('1500x1500') == settings.PLACEHOLDER_IMAGES[30]
