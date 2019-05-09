"""Auto-generated file, do not edit by hand. TM metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_TM = PhoneMetadata(id='TM', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='0\\d', possible_length=(2,)),
    toll_free=PhoneNumberDesc(national_number_pattern='0[1-3]', example_number='01', possible_length=(2,)),
    emergency=PhoneNumberDesc(national_number_pattern='0[1-3]', example_number='01', possible_length=(2,)),
    short_code=PhoneNumberDesc(national_number_pattern='0[1-3]', example_number='01', possible_length=(2,)),
    short_data=True)
