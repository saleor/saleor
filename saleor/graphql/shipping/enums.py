from ...graphql.core.enums import to_enum
from ...shipping import PostalCodeRuleInclusionType, ShippingMethodType
from ..core.doc_category import DOC_CATEGORY_SHIPPING

ShippingMethodTypeEnum = to_enum(ShippingMethodType, type_name="ShippingMethodTypeEnum")
ShippingMethodTypeEnum.doc_category = DOC_CATEGORY_SHIPPING

PostalCodeRuleInclusionTypeEnum = to_enum(
    PostalCodeRuleInclusionType, type_name="PostalCodeRuleInclusionTypeEnum"
)
PostalCodeRuleInclusionTypeEnum.doc_category = DOC_CATEGORY_SHIPPING
