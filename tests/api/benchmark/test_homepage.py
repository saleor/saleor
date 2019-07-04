import pytest

from tests.api.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrieve_main_menu(api_client, count_queries):
    query = """
        fragment MainMenuSubItem on MenuItem {
          id
          name
          category {
            id
            name
          }
          url
          collection {
            id
            name
          }
          page {
            slug
          }
          parent {
            id
          }
        }

        query MainMenu {
          shop {
            navigation {
              main {
                id
                items {
                  ...MainMenuSubItem
                  children {
                    ...MainMenuSubItem
                    children {
                      ...MainMenuSubItem
                    }
                  }
                }
              }
            }
          }
        }
    """

    get_graphql_content(api_client.post_graphql(query))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrieve_secondary_menu(api_client, count_queries):
    query = """
        fragment SecondaryMenuSubItem on MenuItem {
          id
          name
          category {
            id
            name
          }
          url
          collection {
            id
            name
          }
          page {
            slug
          }
        }

        query SecondaryMenu {
          shop {
            navigation {
              secondary {
                items {
                  ...SecondaryMenuSubItem
                  children {
                    ...SecondaryMenuSubItem
                  }
                }
              }
            }
          }
        }
    """
    get_graphql_content(api_client.post_graphql(query))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrieve_shop(api_client, count_queries):
    query = """
        query getShop {
          shop {
            defaultCountry {
              code
              country
            }
            countries {
              country
              code
            }
            geolocalization {
              country {
                code
                country
              }
            }
          }
        }
    """

    get_graphql_content(api_client.post_graphql(query))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrieve_product_list(api_client, count_queries):
    query = """
        query ProductsList {
          shop {
            description
            name
            homepageCollection {
              id
              backgroundImage {
                url
              }
              name
            }
          }
          categories(level: 0, first: 4) {
            edges {
              node {
                id
                name
                backgroundImage {
                  url
                }
              }
            }
          }
        }
    """
    get_graphql_content(api_client.post_graphql(query))
