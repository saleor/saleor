"""Auto-generated file, do not edit by hand. SL metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_SL = PhoneMetadata(id='SL', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[069]\\d\\d(?:\\d{2})?', possible_length=(3, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='(?:01|99)9', example_number='019', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='(?:01|99)9', example_number='019', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='(?:01|99)9|60400', example_number='019', possible_length=(3, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='604\\d\\d', example_number='60400', possible_length=(5,)),
    sms_services=PhoneNumberDesc(national_number_pattern='604\\d\\d', example_number='60400', possible_length=(5,)),
    short_data=True)
