from ...graphql.core.enums import to_enum
from ...warehouse import WarehouseClickAndCollectOption
from ..core.doc_category import DOC_CATEGORY_PRODUCTS

WarehouseClickAndCollectOptionEnum = to_enum(
    WarehouseClickAndCollectOption, type_name="WarehouseClickAndCollectOptionEnum"
)
WarehouseClickAndCollectOptionEnum.doc_category = DOC_CATEGORY_PRODUCTS
