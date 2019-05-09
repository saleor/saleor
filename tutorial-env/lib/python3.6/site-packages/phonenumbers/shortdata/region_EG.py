"""Auto-generated file, do not edit by hand. EG metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_EG = PhoneMetadata(id='EG', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[13]\\d\\d(?:\\d{2})?', possible_length=(3, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:2[23]|80)', example_number='122', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:2[23]|80)', example_number='122', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:2[23]|[69]\\d{3}|80)|34400', example_number='122', possible_length=(3, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='344\\d\\d', example_number='34400', possible_length=(5,)),
    sms_services=PhoneNumberDesc(national_number_pattern='344\\d\\d', example_number='34400', possible_length=(5,)),
    short_data=True)
