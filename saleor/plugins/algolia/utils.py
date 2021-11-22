import graphene
from django.contrib.sites.models import Site
from django.http import HttpRequest
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
from gql import gql

from saleor.account.models import User
from saleor.discount.utils import fetch_discounts
from saleor.graphql.product.schema import ProductQueries
from saleor.plugins.manager import get_plugins_manager
from saleor.product.models import Product


class UserAdminContext(HttpRequest):
    def __init__(self):
        super().__init__()
        self.app = None
        self.request_time = timezone.now()
        self.site = Site.objects.get_current()
        self.user = User.objects.filter(is_staff=True).first()
        self.plugins = SimpleLazyObject(lambda: get_plugins_manager())
        self.discounts = SimpleLazyObject(lambda: fetch_discounts(self.request_time))
        self.META = {
            "header": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8000",
        }


GET_PRODUCT_QUERY = gql(
    """
query GET_PRODUCT($id: ID!, $languageCode: LanguageCodeEnum!) {
  product(id: $id, channel: "default-channel") {
    name
    description
    isAvailable
    slug
    thumbnail {
      url
    }
    metadata {
      key
      value
    }
    pricing {
      priceRange {
        start {
          currency
          net {
            amount
          }
          gross {
            amount
          }
          tax {
            amount
          }
        }
      }
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


def get_product_data(product: "Product", locale="EN"):
    schema = graphene.Schema(query=ProductQueries, types=[Product])

    product_global_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"id": product_global_id, "languageCode": locale}

    product_data = schema.execute(
        GET_PRODUCT_QUERY, variables=variables, context=UserAdminContext()
    )
    product_dict = product_data.data.get("product")
    is_available = product_dict.pop("isAvailable") if product_dict else None
    if not product_data.errors and is_available:
        product_dict.update(
            {
                "objectID": product_global_id,
                "categoryPageId": category_page_id(),
                "gender": product.get_value_from_metadata("gender"),
                "hierarchicalCategories": hierarchical_categories(product),
            }
        )
        return product_dict
