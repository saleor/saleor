"""Auto-generated file, do not edit by hand. WS metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_WS = PhoneMetadata(id='WS', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[19]\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='9(?:11|9[4-69])', example_number='911', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='9(?:11|9[4-69])', example_number='911', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:1[12]|2[0-6])|9(?:11|9[4-79])', example_number='111', possible_length=(3,)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='12[0-6]', example_number='120', possible_length=(3,)),
    short_data=True)
