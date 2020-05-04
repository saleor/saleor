import pytest

from tests.api.utils import get_graphql_content


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
def test_retrieve_product_list(
    api_client, homepage_collection, category, categories_tree, count_queries,
):
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


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_featured_products_list(api_client, homepage_collection, count_queries):
    query = """
        fragment BasicProductFields on Product {
          id
          name
          thumbnail {
            url
            alt
          }
          thumbnail2x: thumbnail(size: 510) {
            url
          }
        }

        fragment Price on TaxedMoney {
          gross {
            amount
            currency
          }
          net {
            amount
            currency
          }
        }

        fragment ProductPricingField on Product {
          pricing {
            onSale
            priceRangeUndiscounted {
              start {
                ...Price
              }
              stop {
                ...Price
              }
            }
            priceRange {
              start {
                ...Price
              }
              stop {
                ...Price
              }
            }
          }
        }

        query FeaturedProducts {
          shop {
            homepageCollection {
              id
              products(first: 20) {
                edges {
                  node {
                    ...BasicProductFields
                    ...ProductPricingField
                    category {
                      id
                      name
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
def test_user_checkout_details(user_api_client, customer_checkout, count_queries):
    query = """
        fragment Price on TaxedMoney {
          gross {
            amount
            currency
          }
          net {
            amount
            currency
          }
        }

        fragment ProductVariant on ProductVariant {
          id
          name
          pricing {
            onSale
            priceUndiscounted {
              ...Price
            }
            price {
              ...Price
            }
          }
          product {
            id
            name
            thumbnail {
              url
              alt
            }
            thumbnail2x: thumbnail(size: 510) {
              url
            }
          }
        }

        fragment CheckoutLine on CheckoutLine {
          id
          quantity
          totalPrice {
            ...Price
          }
          variant {
            stockQuantity
            ...ProductVariant
          }
          quantity
        }

        fragment Address on Address {
          id
          firstName
          lastName
          companyName
          streetAddress1
          streetAddress2
          city
          postalCode
          country {
            code
            country
          }
          countryArea
          phone
          isDefaultBillingAddress
          isDefaultShippingAddress
        }

        fragment ShippingMethod on ShippingMethod {
          id
          name
          price {
            currency
            amount
          }
        }

        fragment Checkout on Checkout {
          availablePaymentGateways {
            id
            name
            config {
              field
              value
            }
          }
          token
          id
          totalPrice {
            ...Price
          }
          subtotalPrice {
            ...Price
          }
          billingAddress {
            ...Address
          }
          shippingAddress {
            ...Address
          }
          email
          availableShippingMethods {
            ...ShippingMethod
          }
          shippingMethod {
            ...ShippingMethod
          }
          shippingPrice {
            ...Price
          }
          lines {
            ...CheckoutLine
          }
          isShippingRequired
          discount {
            currency
            amount
          }
          discountName
          translatedDiscountName
          voucherCode
        }

        query UserCheckoutDetails {
          me {
            id
            checkout {
              ...Checkout
            }
          }
        }
    """
    get_graphql_content(user_api_client.post_graphql(query))
