"""Auto-generated file, do not edit by hand. IL metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_IL = PhoneMetadata(id='IL', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d{2,4}', possible_length=(3, 4, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:0[0-2]|12)', example_number='100', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:0[0-2]|12)', example_number='100', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:0(?:[0-2]|400)|1(?:[013-9]\\d|2)|[2-9]\\d\\d)', example_number='100', possible_length=(3, 4, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='104\\d\\d', example_number='10400', possible_length=(5,)),
    sms_services=PhoneNumberDesc(national_number_pattern='104\\d\\d', example_number='10400', possible_length=(5,)),
    short_data=True)
