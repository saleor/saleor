from django.db.models import Model
from django.test import Client, RequestFactory
from django.urls import reverse
from unittest import mock

from versatileimagefield.datastructures import SizedImage

from saleor.core.utils.warmer import Warmer
from saleor.userprofile.models import User
from saleor.homepage.models import HomePageItem
from saleor.dashboard.homepage import views, urls
from tests.conftest import product_image


BASE_ENDPOINT = 'dashboard:homepage-blocks-'


def test_homepage_block_test_permissions(staff_client, authorized_client):
    clients = (staff_client, authorized_client)
    for url in urls.urlpatterns:
        for client in clients:
            kwargs = {}
            pattern = url.pattern \
                if hasattr(url, 'pattern') else url.regex.pattern

            if '<pk>' in str(pattern):
                kwargs = {'pk': 1}

            path = reverse('dashboard:' + url.name, kwargs=kwargs)
            assert client.get(path).status_code == 302


def test_homepage_block_zero_page(admin_client: Client):
    assert HomePageItem.objects.count() == 0
    resp = admin_client.get(reverse(BASE_ENDPOINT + 'list'))
    assert resp.status_code == 200
    assert b'No blocks found.' in resp.content


def test_homepage_block_list(admin_user: User):
    assert HomePageItem.objects.count() == 0

    request = RequestFactory().get(reverse(BASE_ENDPOINT + 'list'))
    request.user = admin_user
    assert not views.homepage_block_list(request).context_data['blocks']

    blocks = [HomePageItem.objects.create(title='dummy 1'),
              HomePageItem.objects.create(title='dummy 2')]

    received_blocks = views.homepage_block_list(request).context_data['blocks']
    assert len(received_blocks) == len(blocks)

    for current_pos, current_block in enumerate(zip(blocks, received_blocks)):
        current_block, current_recv_block = current_block
        assert current_recv_block.position == current_block\
            .position == current_pos
        assert current_recv_block.pk == current_block.pk


def test_homepage_block_delete(
        admin_client: Client, homepage_block: HomePageItem):
    assert HomePageItem.objects.count() == 1
    endpoint = reverse(
        BASE_ENDPOINT + 'delete', kwargs={'pk': homepage_block.pk})

    resp = admin_client.get(endpoint)
    assert resp.status_code == 200
    assert homepage_block.title in resp.content.decode('utf-8')
    assert HomePageItem.objects.count() == 1

    resp = admin_client.post(endpoint)
    assert resp.status_code == 302
    assert HomePageItem.objects.count() == 0


def test_homepage_block_add__bad_form(
        admin_client: Client, default_category, product_image):
    assert HomePageItem.objects.count() == 0

    resp = admin_client.post(
        reverse(BASE_ENDPOINT + 'add'), {
            'subtitle': 'dummy sub',
            'cover': product_image,
            'category': default_category.pk
        })

    assert resp.status_code == 400
    assert HomePageItem.objects.count() == 0


def test_homepage_block_add__missing_target(
        admin_client: Client, product_image):
    assert HomePageItem.objects.count() == 0

    resp = admin_client.post(
        reverse(BASE_ENDPOINT + 'add'), {
            'title': 'dummy title',
            'subtitle': 'dummy sub',
            'cover': product_image,
        })

    assert resp.status_code == 400
    assert HomePageItem.objects.count() == 0


def test_homepage_block_add__too_many_targets(
        admin_client: Client,
        default_category, collection, page, product_image):
    assert HomePageItem.objects.count() == 0

    resp = admin_client.post(
        reverse(BASE_ENDPOINT + 'add'), {
            'title': 'dummy title',
            'subtitle': 'dummy sub',
            'cover': product_image,
            'category': default_category.pk,
            'page': page.pk
        })

    assert resp.status_code == 400
    assert HomePageItem.objects.count() == 0

    resp = admin_client.post(
        reverse(BASE_ENDPOINT + 'add'), {
            'title': 'dummy title',
            'subtitle': 'dummy sub',
            'cover': product_image,
            'category': default_category.pk,
            'page': page.pk,
            'collection': collection.pk
        })

    assert resp.status_code == 400
    assert HomePageItem.objects.count() == 0


def test_homepage_block_add(
        admin_client: Client, default_category, product_image):
    assert HomePageItem.objects.count() == 0

    with mock.patch.object(Warmer, '__call__') as mocked:
        resp = admin_client.post(
            reverse(BASE_ENDPOINT + 'add'), {
                'title': 'dummy title',
                'subtitle': 'dummy sub',
                'cover': product_image,
                'category': default_category.pk
            })

        assert resp.status_code == 302
        assert HomePageItem.objects.count() == 1

        block = HomePageItem.objects.first()  # type: HomePageItem

        assert block.position == 0

        assert block.title == 'dummy title'
        assert block.subtitle == 'dummy sub'
        assert block.cover is not None

        assert isinstance(block.category, type(default_category))
        assert block.category.pk == default_category.pk

        assert block.linked_object
        assert block.linked_object == block.category

        assert mocked.call_count == 1


def test_homepage_block_edit(
        admin_client: Client, homepage_block,
        default_category, page, collection):

    assert HomePageItem.objects.count() == 1

    with mock.patch.object(SizedImage, 'create_resized_image'):
        def _test(
                data: dict, expected_target: Model,
                expected_warmup: bool, expected_status):
            with mock.patch.object(Warmer, '__call__') as mocked:
                resp = admin_client.post(
                    data=data,
                    path=reverse(
                        BASE_ENDPOINT + 'edit', kwargs={'pk': homepage_block.pk}))

                assert resp.status_code == expected_status
                assert HomePageItem.objects.count() == 1

                if expected_status == 302:
                    block = HomePageItem.objects.first()  # type: HomePageItem

                    assert block.position == 0

                    assert block.title == data['title']
                    assert block.subtitle == data.get('subtitle', None)
                    assert block.cover is not None

                    assert block.linked_object
                    assert isinstance(
                        block.linked_object, type(expected_target))
                    assert block.linked_object.pk == expected_target.pk

                if expected_warmup:
                    assert mocked.call_count == 1
                else:
                    assert mocked.call_count == 0

        _test({
            'title': 'new dummy title',
            'subtitle': 'new dummy sub',
            'cover': product_image(),
            'category': default_category.pk
        }, default_category, True, 302)

        _test({
            'title': 'new dummy title',
            'subtitle': 'new dummy sub',
            'cover': product_image(),
            'page': page.pk
        }, page, True, 302)

        _test({
            'title': 'new dummy title',
            'subtitle': 'new dummy sub',
            'collection': collection.pk
        }, collection, False, 302)

        _test({
            'title': 'new dummy title',
            'subtitle': 'new dummy sub',
            'cover': product_image(),
            'page': page.pk,
            'collection': collection.pk
        }, collection, False, 400)
