"""Auto-generated file, do not edit by hand. HK metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_HK = PhoneMetadata(id='HK', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[19]\\d{2,6}', possible_length=(3, 4, 5, 6, 7)),
    toll_free=PhoneNumberDesc(national_number_pattern='112|99[29]', example_number='112', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='112|99[29]', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:0(?:(?:[0136]\\d|2[14])\\d{0,3}|8[138])|12|2(?:[0-3]\\d{0,4}|(?:58|8[13])\\d{0,3})|7(?:[135-9]\\d{0,4}|219\\d{0,2})|8(?:0(?:(?:[13]|60\\d)\\d|8)|1(?:0\\d|[2-8])|2(?:0[5-9]|(?:18|2)2|3|8[128])|(?:(?:3[0-689]\\d|7(?:2[1-389]|8[0235-9]|93))\\d|8)\\d|50[138]|6(?:1(?:11|86)|8)))|99[29]|10[0139]', example_number='100', possible_length=(3, 4, 5, 6, 7)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='109|1(?:08|85\\d)\\d', example_number='109', possible_length=(3, 4, 5)),
    sms_services=PhoneNumberDesc(national_number_pattern='992', example_number='992', possible_length=(3,)),
    short_data=True)
