"""Auto-generated file, do not edit by hand. GP metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_GP = PhoneMetadata(id='GP', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d', possible_length=(2,)),
    toll_free=PhoneNumberDesc(national_number_pattern='1[578]', example_number='15', possible_length=(2,)),
    emergency=PhoneNumberDesc(national_number_pattern='1[578]', example_number='15', possible_length=(2,)),
    short_code=PhoneNumberDesc(national_number_pattern='1[578]', example_number='15', possible_length=(2,)),
    short_data=True)
