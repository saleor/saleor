"""Auto-generated file, do not edit by hand. CV metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_CV = PhoneMetadata(id='CV', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='13[0-2]', example_number='130', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='13[0-2]', example_number='130', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='13[0-2]', example_number='130', possible_length=(3,)),
    short_data=True)
