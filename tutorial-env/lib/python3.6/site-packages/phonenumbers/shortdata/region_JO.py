"""Auto-generated file, do not edit by hand. JO metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_JO = PhoneMetadata(id='JO', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[19]\\d\\d(?:\\d{2})?', possible_length=(3, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:12|9[127])|911', example_number='112', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:12|9[127])|911', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:09|1[0-2]|9[0-24-79])|9(?:0903|11|8788)', example_number='109', possible_length=(3, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='9(?:09|87)\\d\\d', example_number='90900', possible_length=(5,)),
    sms_services=PhoneNumberDesc(national_number_pattern='9(?:09|87)\\d\\d', example_number='90900', possible_length=(5,)),
    short_data=True)
