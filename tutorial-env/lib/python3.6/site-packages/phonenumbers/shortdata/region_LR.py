"""Auto-generated file, do not edit by hand. LR metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_LR = PhoneMetadata(id='LR', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[3489]\\d{2,3}', possible_length=(3, 4)),
    toll_free=PhoneNumberDesc(national_number_pattern='355|911', example_number='355', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='355|911', example_number='355', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='355|4040|8(?:400|933)|911', example_number='355', possible_length=(3, 4)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='(?:404|8(?:40|93))\\d', example_number='4040', possible_length=(4,)),
    sms_services=PhoneNumberDesc(national_number_pattern='(?:404|8(?:40|93))\\d', example_number='4040', possible_length=(4,)),
    short_data=True)
