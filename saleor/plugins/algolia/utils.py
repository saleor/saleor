from typing import Dict

import graphene
from algoliasearch.search_client import SearchClient
from django.contrib.auth.models import Permission
from django.contrib.sites.models import Site
from django.http import HttpRequest
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
from gql import gql

from saleor.account.models import User
from saleor.celeryconf import app
from saleor.core.permissions import ProductPermissions
from saleor.discount.utils import fetch_discounts
from saleor.graphql.core.utils import from_global_id_or_error
from saleor.graphql.product.schema import ProductQueries
from saleor.plugins.manager import get_plugins_manager
from saleor.product.models import Product


class UserAdminContext(HttpRequest):
    def __init__(self):
        super().__init__()
        self.app = None
        self.request_time = timezone.now()
        self.site = Site.objects.get_current()
        self.plugins = SimpleLazyObject(lambda: get_plugins_manager())
        self.user, _ = User.objects.get_or_create(
            is_staff=True, is_active=True, email="manage@products.com"
        )
        self.user.user_permissions.add(
            Permission.objects.get(codename=ProductPermissions.MANAGE_PRODUCTS.codename)
        )
        self.discounts = SimpleLazyObject(lambda: fetch_discounts(self.request_time))
        self.META = {
            "header": "http",
            "SERVER_PORT": "8000",
            "SERVER_NAME": "localhost",
        }


GET_PRODUCT_QUERY = gql(
    """
query GET_PRODUCTS($id: ID!, $languageCode: LanguageCodeEnum!) {
  products(first: 1, filter: { ids: [$id] }) {
    edges {
      node {
        name
        slug
        collections {
          id
          name
          slug
        }
        metadata {
          key
          value
        }
        description
        media {
          url
        }
        variants {
          id
          sku
          name
          attributes {
            attribute {
              id
              name
              translation(languageCode: $languageCode) {
                name
              }
            }
            values {
              id
              name
              translation(languageCode: $languageCode) {
                name
              }
            }
          }
          translation(languageCode: $languageCode) {
            name
          }
        }
        channelListings {
          pricing {
            priceRange {
              start {
                net {
                  amount
                }
                gross {
                  amount
                }
                tax {
                  amount
                }
                currency
              }
            }
          }
          channel {
            slug
          }
          isPublished
          isAvailableForPurchase
        }
        translation(languageCode: $languageCode) {
          name
          description
        }
        attributes {
          attribute {
            name
            translation(languageCode: $languageCode) {
              name
            }
          }
          values {
            name
            translation(languageCode: $languageCode) {
              name
            }
          }
        }
      }
    }
  }
}
"""
)


def category_page_id():
    return [
        "Products",
        "Categories",
    ]


def hierarchical_categories(product: Product):
    hierarchical = {}
    hierarchical_list = []
    if product.category:
        categories = product.category.get_ancestors(include_self=True)
        for index, category in enumerate(categories):
            hierarchical_list.append(str(category))
            hierarchical.update(
                {
                    "lvl{0}".format(str(index)): " > ".join(
                        hierarchical_list[: index + 1]
                    )
                    if index != 0
                    else hierarchical_list[index]
                }
            )
        return hierarchical


def get_product_data(product_global_id: str, locale="EN"):
    schema = graphene.Schema(query=ProductQueries, types=[Product])

    pk = from_global_id_or_error(product_global_id, "Product")[1]
    product = Product.objects.get(pk=pk)
    variables = {"id": product_global_id, "languageCode": locale}

    product_data = schema.execute(
        GET_PRODUCT_QUERY, variables=variables, context=UserAdminContext()
    )
    product_dict = product_data.data.get("products").get("edges")[0].get("node")
    channels = []
    channel_listings = product_dict.pop("channelListings")
    for channel in channel_listings:
        if channel.get("isAvailableForPurchase") and channel.get("isPublished"):
            channels.append(channel)

    if not product_data.errors and channels:
        product_dict.pop("metadata")
        slug = product_dict.pop("slug")
        images = product_dict.pop("media", [])[:2]
        product_dict.update(
            {
                "objectID": slug,
                "images": images,
                "channels": channels,
                "categoryPageId": category_page_id(),
                "gender": product.get_value_from_metadata("gender"),
                "hierarchicalCategories": hierarchical_categories(product),
            }
        )
        return product_dict


def get_algolia_indices(config: Dict, locale: str):
    client = SearchClient.create(
        api_key=config["ALGOLIA_API_KEY"],
        app_id=config["ALGOLIA_APPLICATION_ID"],
    )

    index = client.init_index(name=f"products_{locale}")
    index.set_settings(
        settings={
            "searchableAttributes": [
                "sku",
                "name",
                "channels",
                "description",
                "translation",
            ]
        }
    )
    return index


@app.task
def index_product_data_to_algolia(
    locale: str, product_global_id: str, sender: str, config: Dict
):
    index = get_algolia_indices(config=config, locale=locale)
    product_data = get_product_data(
        locale=locale,
        product_global_id=product_global_id,
    )
    if product_data:
        if sender == "product_created":
            index.save_object(
                obj=product_data,
                request_options={"autoGenerateObjectIDIfNotExist": False},
            )
        elif sender == "product_updated":
            index.partial_update_object(
                obj=product_data, request_options={"createIfNotExists": True}
            )
        elif sender == "product_deleted":
            # Object ID is required to delete an object, it's the product slug.
            index.delete_object(object_id=product_data.get("objectID"))
        return {
            "locale": locale,
            "sender": sender,
            "product": product_data.get("objectID"),
        }
