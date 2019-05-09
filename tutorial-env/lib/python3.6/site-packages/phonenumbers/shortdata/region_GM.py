"""Auto-generated file, do not edit by hand. GM metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_GM = PhoneMetadata(id='GM', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d\\d?', possible_length=(2, 3)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:1[6-8]|[6-8])', example_number='16', possible_length=(2, 3)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:1[6-8]|[6-8])', example_number='16', possible_length=(2, 3)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:1[6-8]|[6-8])', example_number='16', possible_length=(2, 3)),
    short_data=True)
