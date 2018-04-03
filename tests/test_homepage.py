from unittest import mock

from versatileimagefield.datastructures import SizedImage

from saleor.homepage.models import (
    HomePageItem, DEFAULT_HTML_CLASSES, DEFAULT_PRIMARY_BTN_TEXT)


def test_homepage_block_properties(homepage_block: HomePageItem):
    assert homepage_block.category is None
    assert homepage_block.collection is None
    assert homepage_block.page is None

    assert homepage_block.linked_object is None

    assert homepage_block.html_classes == DEFAULT_HTML_CLASSES
    assert homepage_block.primary_button == 'Dummy button'

    assert homepage_block.url == '#'
    assert homepage_block.cover_url == '/static/images/placeholder540x540.png'


def test_homepage_block_set_cover(homepage_block: HomePageItem, product_image):
    homepage_block.cover = product_image
    assert homepage_block.cover is not None

    with mock.patch.object(SizedImage, 'create_resized_image'):
        assert homepage_block.cover_url == (
            '/media/__sized__/product-thumbnail-1080x720-70.jpg')


def test_homepage_block_set_target(
        homepage_block: HomePageItem,
        default_category, collection, page):

    targets = {
        'category': default_category,
        'collection': collection,
        'page': page,
    }

    def set_target(k, v):
        setattr(homepage_block, k, v)

    def get_target(k):
        return getattr(homepage_block, k)

    def reset():
        for k in targets.keys():
            set_target(k, None)

    for attr, value in targets.items():
        set_target(attr, value)

        assert get_target(attr) is value
        assert homepage_block.linked_object is value
        assert homepage_block.url == value.get_absolute_url()

        reset()

    assert homepage_block.url == '#'


def test_homepage_block_primary_button(homepage_block: HomePageItem):
    assert homepage_block.primary_button == 'Dummy button'

    homepage_block.primary_button_text = None
    assert homepage_block.primary_button == DEFAULT_PRIMARY_BTN_TEXT
