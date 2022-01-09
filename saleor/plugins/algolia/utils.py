from decimal import Decimal
from typing import Dict

import graphene
from algoliasearch.search_client import SearchClient
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.sites.models import Site
from django.http import HttpRequest
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
from gql import gql

from saleor.account.models import User
from saleor.core.permissions import ProductPermissions
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
                  currency
                }
              }
            }
          }
          channel {
            slug
          }
          isPublished
          isAvailableForPurchase
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


def map_product_description(description: dict):
    return description.get("blocks", [{}])[0].get("data", {}).get("text", {})


def map_product_attributes(product_dict: dict, language_code: str):
    attributes = product_dict.get("attributes", [])

    attrs = []
    attrs_ar = []
    if attributes:
        for attribute in attributes:
            attr_dict = {}
            attr_dict_ar = {}
            attr_dict.update(
                {
                    f"{attribute.get('attribute').get('name')}": [
                        value.get("name") for value in attribute.get("values")
                    ]
                    if attribute.get("values")
                    else []
                }
            )
            attribute_key = attribute.get("attribute").get("translation")
            if attribute_key:
                attr_dict_ar.update(
                    {
                        attribute_key.get("name"): [
                            value.get("translation").get("name")
                            for value in attribute.get("values")
                            if value.get("translation")
                        ]
                        if attribute.get("values")
                        else []
                    }
                )
            attrs.append(attr_dict)
            attrs_ar.append(attr_dict_ar)
        return attrs if language_code == "EN" else attrs_ar


def map_product_media(media: list):
    return [url.get("url") for url in media if url.get("url")]


def map_product_collections(product: Product, language_code: str):
    collections = product.collections.all()
    if not collections:
        return []
    elif collections and language_code == "EN":
        return [collection.name for collection in collections]
    else:
        collection_translation = []
        for c in collections:
            translations = c.translations.filter(language_code=language_code)
            for translation in translations:
                collection_translation.append(translation.name)
        return collection_translation


def get_product_data(product_pk: int, language_code="EN"):
    product = Product.objects.get(pk=product_pk)
    schema = graphene.Schema(query=ProductQueries, types=[Product])
    product_global_id = graphene.Node.to_global_id("Product", product_pk)
    variables = {"id": product_global_id, "languageCode": language_code.upper()}

    product_data = schema.execute(
        GET_PRODUCT_QUERY, variables=variables, context=UserAdminContext()
    )
    product_dict = product_data.data.get("products").get("edges")[0].get("node")

    translated_product = product.translations.filter(
        language_code=language_code
    ).first()

    name = ""
    if language_code == "EN":
        name = product.name
    elif translated_product and language_code != "EN":
        name = translated_product.name

    description = {}
    if language_code == "EN":
        description = product.description if product.description else {}
    elif translated_product and language_code != "EN":
        description = translated_product.description

    description = map_product_description(
        description=description,
    )

    attributes = map_product_attributes(
        product_dict=product_dict, language_code=language_code
    )

    channels = []
    channel_listings = product_dict.pop("channelListings")
    for channel in channel_listings:
        price_net = (
            channel.pop("pricing", {})
            .pop("priceRange", {})
            .pop("start", {})
            .pop("net", {})
        )
        is_published = channel.pop("isPublished", False)
        is_available_for_purchase = channel.pop("isAvailableForPurchase", False)

        if is_available_for_purchase and is_published:
            channel.update(
                {
                    "currency": price_net.pop("currency", 0),
                    "name": channel.pop("channel").get("slug"),
                    "price": Decimal(price_net.pop("amount", 0)),
                }
            )
            channels.append(channel)

    if not product_data.errors and channels:
        product_dict.pop("metadata")
        slug = product_dict.pop("slug")
        media = product_dict.pop("media", [])[:2]
        product_dict.update(
            {
                "name": name,
                "objectID": slug,
                "channels": channels,
                "attributes": attributes,
                "description": description,
                # "categoryPageId": category_page_id(),
                "images": map_product_media(media=media),
                "gender": product.get_value_from_metadata("gender"),
                "hierarchicalCategories": hierarchical_categories(product=product),
                "collections": map_product_collections(
                    product=product, language_code=language_code.lower()
                ),
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
                "name",
                "channels",
                "description",
            ]
        }
    )
    return index


def get_locales():
    """Return upper case language locales."""
    locales = []
    for locale in settings.LANGUAGES:
        locales.append(locale[0])
    return locales
