"""Owner-type lookup tables for media.

Media rows live on one table but are exposed as one GraphQL type per owner, and
their global IDs are owner-typed. These maps are the single source of truth for
that correspondence; they live in the domain layer because the webhook payload
and dispatch paths need them as much as the GraphQL layer does.
"""

from ..page import models as page_models
from ..permission.enums import BasePermissionEnum, PagePermissions, ProductPermissions
from . import MediaOwnerTypes
from . import models as product_models

OWNER_TYPE_TO_MODEL: dict[str, type] = {
    MediaOwnerTypes.PRODUCT: product_models.Product,
    MediaOwnerTypes.CATEGORY: product_models.Category,
    MediaOwnerTypes.COLLECTION: product_models.Collection,
    MediaOwnerTypes.PAGE: page_models.Page,
}

# GraphQL enum member name (`PRODUCT`) -> stored owner type (`product`).
ENUM_NAME_TO_OWNER_TYPE: dict[str, str] = {
    owner_type.upper(): owner_type for owner_type in MediaOwnerTypes.ALL
}

OWNER_TYPE_TO_GRAPHQL_TYPE: dict[str, str] = {
    MediaOwnerTypes.PRODUCT: "Product",
    MediaOwnerTypes.CATEGORY: "Category",
    MediaOwnerTypes.COLLECTION: "Collection",
    MediaOwnerTypes.PAGE: "Page",
}
GRAPHQL_TYPE_TO_OWNER_TYPE = {
    graphql_type: owner_type
    for owner_type, graphql_type in OWNER_TYPE_TO_GRAPHQL_TYPE.items()
}

OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE: dict[str, str] = {
    MediaOwnerTypes.PRODUCT: "ProductMedia",
    MediaOwnerTypes.CATEGORY: "CategoryMedia",
    MediaOwnerTypes.COLLECTION: "CollectionMedia",
    MediaOwnerTypes.PAGE: "PageMedia",
}
MEDIA_GRAPHQL_TYPE_TO_OWNER_TYPE = {
    media_type: owner_type
    for owner_type, media_type in OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE.items()
}

MEDIA_OWNER_PERMISSION_MAP: dict[str, BasePermissionEnum] = {
    MediaOwnerTypes.PRODUCT: ProductPermissions.MANAGE_PRODUCTS,
    MediaOwnerTypes.CATEGORY: ProductPermissions.MANAGE_PRODUCTS,
    MediaOwnerTypes.COLLECTION: ProductPermissions.MANAGE_PRODUCTS,
    MediaOwnerTypes.PAGE: PagePermissions.MANAGE_PAGES,
}

# Owner event fired alongside every media change, for storefront cache busting.
OWNER_TYPE_TO_UPDATED_EVENT: dict[str, str] = {
    MediaOwnerTypes.PRODUCT: "product_updated",
    MediaOwnerTypes.CATEGORY: "category_updated",
    MediaOwnerTypes.COLLECTION: "collection_updated",
    MediaOwnerTypes.PAGE: "page_updated",
}
