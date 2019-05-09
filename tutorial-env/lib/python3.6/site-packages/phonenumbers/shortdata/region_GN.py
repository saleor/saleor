"""Auto-generated file, do not edit by hand. GN metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_GN = PhoneMetadata(id='GN', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='4\\d{4}', possible_length=(5,)),
    short_code=PhoneNumberDesc(national_number_pattern='40404', example_number='40404', possible_length=(5,)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='404\\d\\d', example_number='40400', possible_length=(5,)),
    sms_services=PhoneNumberDesc(national_number_pattern='404\\d\\d', example_number='40400', possible_length=(5,)),
    short_data=True)
