"""Auto-generated file, do not edit by hand. PE metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_PE = PhoneMetadata(id='PE', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:05|1[67])', example_number='105', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:05|1[67])', example_number='105', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:05|1[67])', example_number='105', possible_length=(3,)),
    short_data=True)
