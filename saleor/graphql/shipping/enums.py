from ...graphql.core.enums import to_enum
from ...shipping import PostalCodeRuleInclusionType, ShippingMethodType
from ..core.doc_category import DOC_CATEGORY_SHIPPING
from ..directives import doc

ShippingMethodTypeEnum = doc(
    DOC_CATEGORY_SHIPPING,
    to_enum(ShippingMethodType, type_name="ShippingMethodTypeEnum"),
)

PostalCodeRuleInclusionTypeEnum = doc(
    DOC_CATEGORY_SHIPPING,
    to_enum(PostalCodeRuleInclusionType, type_name="PostalCodeRuleInclusionTypeEnum"),
)
