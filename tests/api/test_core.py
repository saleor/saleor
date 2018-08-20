import json
from unittest.mock import Mock

import graphene
from django.conf import settings
from django.shortcuts import reverse
from django_countries import countries
from django_prices_vatlayer.models import VAT
from tests.utils import get_graphql_content

from saleor.core.permissions import MODELS_PERMISSIONS
from saleor.graphql.core.utils import clean_seo_fields, snake_to_camel_case
from saleor.graphql.product import types as product_types
from saleor.graphql.utils import get_database_id

from .utils import assert_no_permission


def test_query_authorization_keys(authorization_key, admin_api_client, user_api_client):
    query = """
    query {
        shop {
            authorizationKeys {
                name
                key
            }
        }
    }
    """
    response = admin_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shop']
    assert data['authorizationKeys'][0]['name'] == authorization_key.name
    assert data['authorizationKeys'][0]['key'] == authorization_key.key

    response = user_api_client.post(reverse('api'), {'query': query})
    assert_no_permission(response)


def test_query_countries(user_api_client):
    query = """
    query {
        shop {
            countries {
                code
                country
            }
        }
    }
    """
    response = user_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shop']
    assert len(data['countries']) == len(countries)


def test_query_currencies(user_api_client):
    query = """
    query {
        shop {
            currencies
            defaultCurrency
        }
    }
    """
    response = user_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shop']
    assert len(data['currencies']) == len(settings.AVAILABLE_CURRENCIES)
    assert data['defaultCurrency'] == settings.DEFAULT_CURRENCY


def test_query_name(user_api_client, site_settings):
    query = """
    query {
        shop {
            name
            description
        }
    }
    """
    response = user_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shop']
    assert data['description'] == site_settings.description
    assert data['name'] == site_settings.site.name


def test_query_domain(user_api_client, site_settings):
    query = """
    query {
        shop {
            domain {
                host
                sslEnabled
                url
            }
        }
    }
    """
    response = user_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shop']
    assert data['domain']['host'] == site_settings.site.domain
    assert data['domain']['sslEnabled'] == settings.ENABLE_SSL
    assert data['domain']['url']


def test_query_tax_rates(admin_api_client, user_api_client, vatlayer):
    vat = VAT.objects.order_by('country_code').first()
    query = """
    query {
        shop {
            taxRates {
                countryCode
                standardRate
                reducedRates {
                    rate
                    rateType
                }
            }
        }
    }
    """
    response = admin_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shop']
    assert data['taxRates'][0]['countryCode'] == vat.country_code
    assert data['taxRates'][0]['standardRate'] == vat.data['standard_rate']
    assert len(data['taxRates'][0]['reducedRates']) == len(vat.data['reduced_rates'])

    response = user_api_client.post(reverse('api'), {'query': query})
    assert_no_permission(response)


def test_query_tax_rate(user_api_client, admin_api_client, vatlayer):
    vat = VAT.objects.order_by('country_code').first()
    query = """
    query taxRate($countryCode: String!) {
        shop {
            taxRate(countryCode: $countryCode) {
                countryCode
            }
        }
    }
    """
    variables = json.dumps({'countryCode': vat.country_code})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shop']
    assert data['taxRate']['countryCode'] == vat.country_code

    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_no_permission(response)


def test_query_languages(settings, user_api_client):
    query = """
    query {
        shop {
            languages {
                code
                language
            }
        }
    }
    """
    response = user_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shop']
    assert len(data['languages']) == len(settings.LANGUAGES)


def test_query_permissions(admin_api_client, user_api_client):
    query = """
    query {
        shop {
            permissions {
                code
                name
            }
        }
    }
    """
    response = admin_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['shop']
    permissions = data['permissions']
    permissions_codes = {permission.get('code') for permission in permissions}
    assert len(permissions_codes) == len(MODELS_PERMISSIONS)
    for code in permissions_codes:
        assert code in MODELS_PERMISSIONS

    response = user_api_client.post(reverse('api'), {'query': query})
    assert_no_permission(response)


def test_clean_seo_fields():
    title = 'lady title'
    description = 'fantasy description'
    data = {'seo':
                {'title': title,
                 'description': description}}
    clean_seo_fields(data)
    assert data['seo_title'] == title
    assert data['seo_description'] == description


def test_user_error_field_name_for_related_object(admin_api_client):
    query = """
    mutation {
        categoryCreate(input: {name: "Test", parent: "123456"}) {
            errors {
                field
                message
            }
            category {
                id
            }
        }
    }
    """
    response = admin_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    data = content['data']['categoryCreate']['category']
    assert data is None
    error = content['data']['categoryCreate']['errors'][0]
    assert error['field'] == 'parent'


def test_get_database_id(product):
    info = Mock(
        schema=Mock(
            get_type=Mock(
                return_value=Mock(graphene_type=product_types.Product))))
    node_id = graphene.Node.to_global_id('Product', product.pk)
    pk = get_database_id(info, node_id, product_types.Product)
    assert int(pk) == product.pk


def test_snake_to_camel_case():
    assert snake_to_camel_case('test_camel_case') == 'testCamelCase'
    assert snake_to_camel_case('testCamel_case') == 'testCamelCase'
    assert snake_to_camel_case(123) == 123


def test_mutation_returns_error_field_in_camel_case(admin_api_client, variant):
    # costPrice is snake case variable (cost_price) in the backend
    query = """
    mutation testCamel($id: ID!, $cost: Decimal) {
        productVariantUpdate(id: $id,
        input: {costPrice: $cost, trackInventory: false}) {
            errors {
                field
                message
            }
            productVariant {
                id
            }
        }
    }
    """
    variables = json.dumps({
        'id': graphene.Node.to_global_id('ProductVariant', variant.id),
        'cost': '12.1234'})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    error = content['data']['productVariantUpdate']['errors'][0]
    assert error['field'] == 'costPrice'
