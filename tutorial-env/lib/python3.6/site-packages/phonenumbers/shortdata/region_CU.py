"""Auto-generated file, do not edit by hand. CU metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_CU = PhoneMetadata(id='CU', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d\\d(?:\\d{3})?', possible_length=(3, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='10[4-6]', example_number='104', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='10[4-6]', example_number='104', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:0[4-6]|1(?:6111|8)|40)', example_number='104', possible_length=(3, 6)),
    short_data=True)
