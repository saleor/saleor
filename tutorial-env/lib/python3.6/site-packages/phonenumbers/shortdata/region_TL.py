"""Auto-generated file, do not edit by hand. TL metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_TL = PhoneMetadata(id='TL', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='11[25]', example_number='112', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='11[25]', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:0[02]|1[25]|2[0138]|72|9[07])', example_number='100', possible_length=(3,)),
    short_data=True)
