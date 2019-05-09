"""Auto-generated file, do not edit by hand. KZ metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_KZ = PhoneMetadata(id='KZ', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[134]\\d{2,4}', possible_length=(3, 4, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:0[1-3]|12)', example_number='101', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:0[1-3]|12)', example_number='101', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:0[1-4]|12)|(?:3040|404)0', example_number='101', possible_length=(3, 4, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='(?:304\\d|404)\\d', example_number='4040', possible_length=(4, 5)),
    sms_services=PhoneNumberDesc(national_number_pattern='(?:304\\d|404)\\d', example_number='4040', possible_length=(4, 5)),
    short_data=True)
