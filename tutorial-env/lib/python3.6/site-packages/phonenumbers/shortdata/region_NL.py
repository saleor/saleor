"""Auto-generated file, do not edit by hand. NL metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_NL = PhoneMetadata(id='NL', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[1349]\\d\\d(?:\\d(?:\\d{2})?)?', possible_length=(3, 4, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='11(?:2|6\\d{3})|911', example_number='112', possible_length=(3, 6)),
    emergency=PhoneNumberDesc(national_number_pattern='112|911', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:1(?:2|6(?:00[06]|1(?:11|23)))|2(?:0[0-4]|3[34]|44)|3[03-9]\\d|400|8(?:[02-9]\\d|1[0-79]))|[34]000|911', example_number='112', possible_length=(3, 4, 6)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='120\\d', example_number='1200', possible_length=(4,)),
    sms_services=PhoneNumberDesc(national_number_pattern='[34]00\\d', example_number='3000', possible_length=(4,)),
    short_data=True)
