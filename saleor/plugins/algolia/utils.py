import graphene
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
        metadata {
          key
          value
        }
        description
        media {
          url
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


@app.task
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
