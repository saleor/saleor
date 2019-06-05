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
            __typename
          }
          url
          collection {
            id
            name
            __typename
          }
          page {
            slug
            __typename
          }
          parent {
            id
            __typename
          }
          __typename
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
                      __typename
                    }
                    __typename
                  }
                  __typename
                }
                __typename
              }
              __typename
            }
            __typename
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
            __typename
          }
          url
          collection {
            id
            name
            __typename
          }
          page {
            slug
            __typename
          }
          __typename
        }

        query SecondaryMenu {
          shop {
            navigation {
              secondary {
                items {
                  ...SecondaryMenuSubItem
                  children {
                    ...SecondaryMenuSubItem
                    __typename
                  }
                  __typename
                }
                __typename
              }
              __typename
            }
            __typename
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
              __typename
            }
            countries {
              country
              code
              __typename
            }
            geolocalization {
              country {
                code
                country
                __typename
              }
              __typename
            }
            __typename
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
                __typename
              }
              name
              __typename
            }
            __typename
          }
          categories(level: 0, first: 4) {
            edges {
              node {
                id
                name
                backgroundImage {
                  url
                  __typename
                }
                __typename
              }
              __typename
            }
            __typename
          }
        }
    """
    get_graphql_content(api_client.post_graphql(query))
