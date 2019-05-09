"""Auto-generated file, do not edit by hand. KH metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_KH = PhoneMetadata(id='KH', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[146]\\d\\d(?:\\d{2})?', possible_length=(3, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='11[7-9]|666', example_number='117', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='11[7-9]|666', example_number='117', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='11[7-9]|40404|666', example_number='117', possible_length=(3, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='404\\d\\d', example_number='40400', possible_length=(5,)),
    sms_services=PhoneNumberDesc(national_number_pattern='404\\d\\d', example_number='40400', possible_length=(5,)),
    short_data=True)
