"""Auto-generated file, do not edit by hand. HU metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_HU = PhoneMetadata(id='HU', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d\\d(?:\\d{3})?', possible_length=(3, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:0[457]|1(?:2|6\\d{3}))', example_number='104', possible_length=(3, 6)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:0[457]|12)', example_number='104', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:0[457]|1(?:2|6(?:000|1(?:11|23))))', example_number='104', possible_length=(3, 6)),
    short_data=True)
