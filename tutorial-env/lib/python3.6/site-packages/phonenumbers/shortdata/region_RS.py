"""Auto-generated file, do not edit by hand. RS metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_RS = PhoneMetadata(id='RS', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[19]\\d{1,5}', possible_length=(2, 3, 4, 5, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='112|9[2-4]', example_number='92', possible_length=(2, 3)),
    emergency=PhoneNumberDesc(national_number_pattern='112|9[2-4]', example_number='92', possible_length=(2, 3)),
    short_code=PhoneNumberDesc(national_number_pattern='1[189]\\d{1,4}|9[2-4]', example_number='92', possible_length=(2, 3, 4, 5, 6)),
    short_data=True)
