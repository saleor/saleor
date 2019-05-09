"""Auto-generated file, do not edit by hand. MR metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_MR = PhoneMetadata(id='MR', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d', possible_length=(2,)),
    toll_free=PhoneNumberDesc(national_number_pattern='1[78]', example_number='17', possible_length=(2,)),
    emergency=PhoneNumberDesc(national_number_pattern='1[78]', example_number='17', possible_length=(2,)),
    short_code=PhoneNumberDesc(national_number_pattern='1[78]', example_number='17', possible_length=(2,)),
    short_data=True)
