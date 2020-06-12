import pytest

from ....tests.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrieve_main_menu(api_client, site_with_top_menu, count_queries):
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
def test_retrieve_secondary_menu(api_client, site_with_bottom_menu, count_queries):
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
