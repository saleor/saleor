"""Auto-generated file, do not edit by hand. CF metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_CF = PhoneMetadata(id='CF', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d{2,3}', possible_length=(3, 4)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:1[78]|22\\d)', example_number='117', possible_length=(3, 4)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:1[78]|220)', example_number='117', possible_length=(3, 4)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:1[478]|220)', example_number='114', possible_length=(3, 4)),
    short_data=True)
