"""Auto-generated file, do not edit by hand. NA metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_NA = PhoneMetadata(id='NA', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[19]\\d{2,4}', possible_length=(3, 4, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='10111', example_number='10111', possible_length=(5,)),
    emergency=PhoneNumberDesc(national_number_pattern='10111', example_number='10111', possible_length=(5,)),
    short_code=PhoneNumberDesc(national_number_pattern='(?:10|93)111|(?:1\\d|9)\\d\\d', example_number='900', possible_length=(3, 4, 5)),
    short_data=True)
