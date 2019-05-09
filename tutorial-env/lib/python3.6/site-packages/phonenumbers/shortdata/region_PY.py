"""Auto-generated file, do not edit by hand. PY metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_PY = PhoneMetadata(id='PY', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[19]\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='128|911', example_number='128', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='128|911', example_number='128', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1[1-4]\\d|911', example_number='110', possible_length=(3,)),
    short_data=True)
