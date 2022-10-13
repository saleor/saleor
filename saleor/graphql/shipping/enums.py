from ...graphql.core.enums import to_enum
from ...shipping import PostalCodeRuleInclusionType, ShippingMethodType

ShippingMethodTypeEnum = to_enum(ShippingMethodType, type_name="ShippingMethodTypeEnum")
PostalCodeRuleInclusionTypeEnum = to_enum(
    PostalCodeRuleInclusionType, type_name="PostalCodeRuleInclusionTypeEnum"
)
