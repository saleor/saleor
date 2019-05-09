"""Auto-generated file, do not edit by hand. GG metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_GG = PhoneMetadata(id='GG', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[19]\\d{2,5}', possible_length=(3, 4, 5, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='112|999', example_number='112', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='112|999', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:0[01]|1[12]|23|41|55|9[05])|999|1(?:1[68]\\d\\d|47|800)\\d', example_number='100', possible_length=(3, 4, 5, 6)),
    short_data=True)
