"""Auto-generated file, do not edit by hand. JP metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_JP = PhoneMetadata(id='JP', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='11[09]', example_number='110', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='11[09]', example_number='110', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='11[09]', example_number='110', possible_length=(3,)),
    short_data=True)
