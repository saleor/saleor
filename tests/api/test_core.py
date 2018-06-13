import json
from tests.utils import get_graphql_content
from django.shortcuts import reverse
from phonenumbers import COUNTRY_CODE_TO_REGION_CODE
from saleor.core.permissions import MODELS_PERMISSIONS


def test_shop_endpoint(settings, admin_api_client):
    query = """
    query shop {
        shop {
            permissions {
                code
                name
            }
            languages {
                code
                language
            }
            phonePrefixes
        }
    }
    """
    languages = settings.LANGUAGES
    response = admin_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)

    assert 'errors' not in content
    data = content['data']['shop']
    permissions = data['permissions']
    permissions_codes = {permission.get('code') for permission in permissions}
    assert len(permissions_codes) == len(MODELS_PERMISSIONS)
    for code in permissions_codes:
        assert code in MODELS_PERMISSIONS
    assert len(data['languages']) == len(languages)
    assert len(data['phonePrefixes']) == len(COUNTRY_CODE_TO_REGION_CODE)

