import json

from django.shortcuts import reverse
from tests.utils import get_graphql_content
from saleor.site.models import Site


def test_query_site_settings(user_api_client, site_settings):
    query = """
        query {
            siteSettings {
                domain,
                includeTaxesInPrices,
                headerText
            }
        }
    """
    response = user_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['siteSettings']
    assert data['domain'] == site_settings.site.domain
    assert data['includeTaxesInPrices'] == site_settings.include_taxes_in_prices
    assert data['headerText'] == site_settings.header_text



def test_site_settings_mutation(user_api_client, site_settings):
    query = """
        mutation updateSettings($input: SiteSettingsInput!) {
            siteSettingsUpdate(input: $input) {
                siteSettings {
                    domain,
                    headerText,
                    includeTaxesInPrices,
                    homepageCollection {
                        id,
                        name
                    }
                }
            }
        }
    """
    new_domain = 'best-store.com'
    variables = json.dumps({
        'input': {
            'domain': new_domain,
            'homepageCollection': None,
            'includeTaxesInPrices': False
        }
    })
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['siteSettingsUpdate']['siteSettings']
    assert data['domain'] == new_domain
    assert data['includeTaxesInPrices'] == False
    assert data['homepageCollection'] == None
    site_settings.refresh_from_db()
    site = Site.objects.get(pk=site_settings.site.pk)
    assert site.domain == new_domain
    assert not site_settings.include_taxes_in_prices
    assert site_settings.homepage_collection is None
