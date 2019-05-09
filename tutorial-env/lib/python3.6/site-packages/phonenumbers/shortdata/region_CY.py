"""Auto-generated file, do not edit by hand. CY metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_CY = PhoneMetadata(id='CY', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d\\d(?:\\d{3})?', possible_length=(3, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:1(?:2|6\\d{3})|99)', example_number='112', possible_length=(3, 6)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:12|99)', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:1(?:2|6(?:000|111))|99)', example_number='112', possible_length=(3, 6)),
    short_data=True)
