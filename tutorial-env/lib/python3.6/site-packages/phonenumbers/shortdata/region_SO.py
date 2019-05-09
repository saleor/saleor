"""Auto-generated file, do not edit by hand. SO metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_SO = PhoneMetadata(id='SO', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[57-9]\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='555|888|999', example_number='555', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='555|888|999', example_number='555', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='555|777|888|999', example_number='555', possible_length=(3,)),
    short_data=True)
