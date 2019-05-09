"""Auto-generated file, do not edit by hand. PA metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_PA = PhoneMetadata(id='PA', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[19]\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='911', example_number='911', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='911', example_number='911', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='10[2-4]|911', example_number='102', possible_length=(3,)),
    short_data=True)
