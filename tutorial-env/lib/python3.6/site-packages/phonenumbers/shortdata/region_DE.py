"""Auto-generated file, do not edit by hand. DE metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_DE = PhoneMetadata(id='DE', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d\\d(?:\\d{3})?', possible_length=(3, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='11(?:[02]|6\\d{3})', example_number='110', possible_length=(3, 6)),
    emergency=PhoneNumberDesc(national_number_pattern='11[02]', example_number='110', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='11(?:[025]|6(?:00[06]|1(?:1[17]|23)))', example_number='110', possible_length=(3, 6)),
    short_data=True)
