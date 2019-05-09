"""Auto-generated file, do not edit by hand. PH metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_PH = PhoneMetadata(id='PH', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[19]\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='11[27]|911', example_number='112', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='11[27]|911', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='11[27]|911', example_number='112', possible_length=(3,)),
    short_data=True)
