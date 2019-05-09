"""Auto-generated file, do not edit by hand. KG metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_KG = PhoneMetadata(id='KG', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[14]\\d{2,3}', possible_length=(3, 4)),
    toll_free=PhoneNumberDesc(national_number_pattern='10[1-3]', example_number='101', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='10[1-3]', example_number='101', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='10[1-3]|4040', example_number='101', possible_length=(3, 4)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='404\\d', example_number='4040', possible_length=(4,)),
    sms_services=PhoneNumberDesc(national_number_pattern='404\\d', example_number='4040', possible_length=(4,)),
    short_data=True)
