"""Auto-generated file, do not edit by hand. FK metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_FK = PhoneMetadata(id='FK', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[19]\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='999', example_number='999', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='999', example_number='999', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1\\d\\d|999', example_number='100', possible_length=(3,)),
    short_data=True)
