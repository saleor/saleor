"""Auto-generated file, do not edit by hand. MN metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_MN = PhoneMetadata(id='MN', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='10[0-3]', example_number='100', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='10[0-3]', example_number='100', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='10[0-3]', example_number='100', possible_length=(3,)),
    short_data=True)
