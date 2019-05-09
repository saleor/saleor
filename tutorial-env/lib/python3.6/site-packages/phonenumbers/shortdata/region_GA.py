"""Auto-generated file, do not edit by hand. GA metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_GA = PhoneMetadata(id='GA', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d(?:\\d{2})?', possible_length=(2, 4)),
    toll_free=PhoneNumberDesc(national_number_pattern='18|1(?:3\\d|73)\\d', example_number='18', possible_length=(2, 4)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:3\\d\\d|730|8)', example_number='18', possible_length=(2, 4)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:3\\d\\d|730|8)', example_number='18', possible_length=(2, 4)),
    short_data=True)
