from .....site.models import Site
from ....tests.utils import get_graphql_content


def test_shop_domain_update(staff_api_client, permission_manage_settings):
    # given
    query = """
        mutation updateSettings($input: SiteDomainInput!) {
            shopDomainUpdate(input: $input) {
                shop {
                    name
                    domain {
                        host,
                    }
                }
            }
        }
    """
    new_name = "saleor test store"
    variables = {"input": {"domain": "lorem-ipsum.com", "name": new_name}}
    site = Site.objects.get_current()
    assert site.domain != "lorem-ipsum.com"

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shopDomainUpdate"]["shop"]
    assert data["domain"]["host"] == "lorem-ipsum.com"
    assert data["name"] == new_name
    site.refresh_from_db()
    assert site.domain == "lorem-ipsum.com"
    assert site.name == new_name
