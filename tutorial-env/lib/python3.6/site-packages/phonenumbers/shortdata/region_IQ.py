"""Auto-generated file, do not edit by hand. IQ metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_IQ = PhoneMetadata(id='IQ', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[1479]\\d{2,4}', possible_length=(3, 4, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:0[04]|15|22)', example_number='100', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:0[04]|15|22)', example_number='100', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:0[04]|15|22)|4432|71117|9988', example_number='100', possible_length=(3, 4, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='(?:443|711\\d|998)\\d', example_number='4430', possible_length=(4, 5)),
    sms_services=PhoneNumberDesc(national_number_pattern='(?:443|711\\d|998)\\d', example_number='4430', possible_length=(4, 5)),
    short_data=True)
