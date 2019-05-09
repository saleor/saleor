"""Auto-generated file, do not edit by hand. GH metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_GH = PhoneMetadata(id='GH', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[14589]\\d{2,4}', possible_length=(3, 4, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='19[1-3]|999', example_number='191', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='19[1-3]|999', example_number='191', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='19[1-3]|40404|(?:54|83)00|999', example_number='191', possible_length=(3, 4, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='404\\d\\d|(?:54|83)0\\d', example_number='5400', possible_length=(4, 5)),
    sms_services=PhoneNumberDesc(national_number_pattern='404\\d\\d|(?:54|83)0\\d', example_number='5400', possible_length=(4, 5)),
    short_data=True)
