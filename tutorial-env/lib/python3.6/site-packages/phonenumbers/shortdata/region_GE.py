"""Auto-generated file, do not edit by hand. GE metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_GE = PhoneMetadata(id='GE', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[014]\\d\\d(?:\\d{2})?', possible_length=(3, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='0(?:11|33)|11[1-3]|[01]22', example_number='011', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='0(?:11|33)|11[1-3]|[01]22', example_number='011', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='0(?:11|33)|11[1-3]|40404|[01]22', example_number='011', possible_length=(3, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='404\\d\\d', example_number='40400', possible_length=(5,)),
    sms_services=PhoneNumberDesc(national_number_pattern='404\\d\\d', example_number='40400', possible_length=(5,)),
    short_data=True)
