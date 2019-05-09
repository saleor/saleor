"""Auto-generated file, do not edit by hand. RO metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_RO = PhoneMetadata(id='RO', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[18]\\d\\d(?:\\d(?:\\d{2})?)?', possible_length=(3, 4, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='11(?:2|6\\d{3})', example_number='112', possible_length=(3, 6)),
    premium_rate=PhoneNumberDesc(national_number_pattern='(?:1(?:18\\d|[24])|8[48])\\d\\d', example_number='1200', possible_length=(4, 6)),
    emergency=PhoneNumberDesc(national_number_pattern='112', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:1(?:2|6111|8932)|[24]\\d\\d|9(?:21|3[02]|5[178]))|8[48]\\d\\d|11(?:60|83)00', example_number='112', possible_length=(3, 4, 6)),
    sms_services=PhoneNumberDesc(national_number_pattern='(?:1[24]|8[48])\\d\\d', example_number='1200', possible_length=(4,)),
    short_data=True)
