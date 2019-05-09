"""Auto-generated file, do not edit by hand. RU metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_RU = PhoneMetadata(id='RU', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[01]\\d\\d?', possible_length=(2, 3)),
    toll_free=PhoneNumberDesc(national_number_pattern='112|(?:0|10)[1-3]', example_number='01', possible_length=(2, 3)),
    emergency=PhoneNumberDesc(national_number_pattern='112|(?:0|10)[1-3]', example_number='01', possible_length=(2, 3)),
    short_code=PhoneNumberDesc(national_number_pattern='112|(?:0|10)[1-4]', example_number='01', possible_length=(2, 3)),
    short_data=True)
