"""Auto-generated file, do not edit by hand. SV metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_SV = PhoneMetadata(id='SV', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[49]\\d\\d(?:\\d{2})?', possible_length=(3, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='911', example_number='911', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='911', example_number='911', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='40404|911', example_number='911', possible_length=(3, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='404\\d\\d', example_number='40400', possible_length=(5,)),
    sms_services=PhoneNumberDesc(national_number_pattern='404\\d\\d', example_number='40400', possible_length=(5,)),
    short_data=True)
