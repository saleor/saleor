"""Auto-generated file, do not edit by hand. EC metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_EC = PhoneMetadata(id='EC', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[19]\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:0[12]|12)|911', example_number='101', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:0[12]|12)|911', example_number='101', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:0[12]|12)|911', example_number='101', possible_length=(3,)),
    short_data=True)
