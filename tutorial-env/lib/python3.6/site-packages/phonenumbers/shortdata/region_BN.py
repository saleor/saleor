"""Auto-generated file, do not edit by hand. BN metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_BN = PhoneMetadata(id='BN', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='9\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='99[135]', example_number='991', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='99[135]', example_number='991', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='99[135]', example_number='991', possible_length=(3,)),
    short_data=True)
