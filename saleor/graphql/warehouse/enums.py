from ...graphql.core.enums import to_enum
from ...warehouse import WarehouseClickAndCollectOption
from ..core.doc_category import DOC_CATEGORY_PRODUCTS
from ..directives import doc

WarehouseClickAndCollectOptionEnum = doc(
    DOC_CATEGORY_PRODUCTS,
    to_enum(
        WarehouseClickAndCollectOption, type_name="WarehouseClickAndCollectOptionEnum"
    ),
)
