"""Auto-generated file, do not edit by hand. FK metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_FK = PhoneMetadata(id='FK', country_code=500, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[2-7]\\d{4}', possible_length=(5,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='[2-47]\\d{4}', example_number='31234', possible_length=(5,)),
    mobile=PhoneNumberDesc(national_number_pattern='[56]\\d{4}', example_number='51234', possible_length=(5,)))
