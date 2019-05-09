"""Auto-generated file, do not edit by hand. ZM metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_ZM = PhoneMetadata(id='ZM', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[19]\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='112|99[139]', example_number='112', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='112|99[139]', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='112|99[139]', example_number='112', possible_length=(3,)),
    short_data=True)
