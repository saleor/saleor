"""Auto-generated file, do not edit by hand. TV metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_TV = PhoneMetadata(id='TV', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[19]\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='911', example_number='911', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='911', example_number='911', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1\\d\\d|911', example_number='100', possible_length=(3,)),
    short_data=True)
