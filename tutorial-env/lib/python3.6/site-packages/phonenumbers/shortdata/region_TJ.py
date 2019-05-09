"""Auto-generated file, do not edit by hand. TJ metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_TJ = PhoneMetadata(id='TJ', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:0[1-3]|12)', example_number='101', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:0[1-3]|12)', example_number='101', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:0[1-3]|12)', example_number='101', possible_length=(3,)),
    short_data=True)
