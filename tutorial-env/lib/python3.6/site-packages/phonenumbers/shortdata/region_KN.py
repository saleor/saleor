"""Auto-generated file, do not edit by hand. KN metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_KN = PhoneMetadata(id='KN', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[39]\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='333|9(?:11|99)', example_number='333', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='333|9(?:11|99)', example_number='333', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='333|9(?:11|99)', example_number='333', possible_length=(3,)),
    short_data=True)
