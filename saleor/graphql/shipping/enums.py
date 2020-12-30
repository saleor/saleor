from ...graphql.core.enums import to_enum
from ...shipping import ShippingMethodType, ZipCodeRuleInclusionType

ShippingMethodTypeEnum = to_enum(ShippingMethodType, type_name="ShippingMethodTypeEnum")
ZipCodeRuleInclusionTypeEnum = to_enum(
    ZipCodeRuleInclusionType, type_name="ZipCodeRuleInclusionTypeEnum"
)
