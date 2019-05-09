"""Auto-generated file, do not edit by hand. AM metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_AM = PhoneMetadata(id='AM', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[148]\\d{2,4}', possible_length=(3, 4, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='10[1-3]', example_number='101', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='10[1-3]', example_number='101', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='(?:1|8[1-7])\\d\\d|40404', example_number='100', possible_length=(3, 4, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='404\\d\\d', example_number='40400', possible_length=(5,)),
    sms_services=PhoneNumberDesc(national_number_pattern='404\\d\\d', example_number='40400', possible_length=(5,)),
    short_data=True)
