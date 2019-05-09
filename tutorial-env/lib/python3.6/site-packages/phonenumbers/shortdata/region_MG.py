"""Auto-generated file, do not edit by hand. MG metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_MG = PhoneMetadata(id='MG', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d\\d?', possible_length=(2, 3)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:1[78]|[78])', example_number='17', possible_length=(2, 3)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:1[78]|[78])', example_number='17', possible_length=(2, 3)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:1[78]|[78])', example_number='17', possible_length=(2, 3)),
    short_data=True)
