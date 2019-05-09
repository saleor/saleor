"""Auto-generated file, do not edit by hand. MU metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_MU = PhoneMetadata(id='MU', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[189]\\d{2,4}', possible_length=(3, 4, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='11[45]|99[59]', example_number='114', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='11[45]|99[59]', example_number='114', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1\\d{2,4}|(?:8\\d\\d|99)\\d', example_number='100', possible_length=(3, 4, 5)),
    short_data=True)
