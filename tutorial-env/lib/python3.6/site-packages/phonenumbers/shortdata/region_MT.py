"""Auto-generated file, do not edit by hand. MT metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_MT = PhoneMetadata(id='MT', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d\\d(?:\\d{3})?', possible_length=(3, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='11(?:2|6\\d{3})', example_number='112', possible_length=(3, 6)),
    emergency=PhoneNumberDesc(national_number_pattern='112', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='11(?:2|6(?:000|1(?:11|23)))', example_number='112', possible_length=(3, 6)),
    short_data=True)
