"""Auto-generated file, do not edit by hand. MX metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_MX = PhoneMetadata(id='MX', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[0579]\\d{2,4}', possible_length=(3, 4, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='0(?:6[0568]|80)|911', example_number='060', possible_length=(3,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='(?:530\\d|776)\\d', example_number='7760', possible_length=(4, 5)),
    emergency=PhoneNumberDesc(national_number_pattern='0(?:6[0568]|80)|911', example_number='060', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='0[1-9]\\d|53053|7766|911', example_number='010', possible_length=(3, 4, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='0(?:[249]0|[35][01])', example_number='020', possible_length=(3,)),
    short_data=True)
