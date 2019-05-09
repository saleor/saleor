"""Auto-generated file, do not edit by hand. CX metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_CX = PhoneMetadata(id='CX', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[01]\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='000|112', example_number='000', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='000|112', example_number='000', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='000|112', example_number='000', possible_length=(3,)),
    short_data=True)
