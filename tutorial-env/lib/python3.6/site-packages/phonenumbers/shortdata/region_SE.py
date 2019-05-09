"""Auto-generated file, do not edit by hand. SE metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_SE = PhoneMetadata(id='SE', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[1-37-9]\\d{2,5}', possible_length=(3, 4, 5, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='112|(?:116\\d|900)\\d\\d', example_number='112', possible_length=(3, 5, 6)),
    premium_rate=PhoneNumberDesc(national_number_pattern='11811[89]|72\\d{3}', example_number='72000', possible_length=(5, 6)),
    emergency=PhoneNumberDesc(national_number_pattern='112|90000', example_number='112', possible_length=(3, 5)),
    short_code=PhoneNumberDesc(national_number_pattern='11(?:[25]|313|6(?:00[06]|1(?:1[17]|23))|7[0-8])|2(?:2[02358]|33|4[01]|50|6[1-4])|32[13]|8(?:22|88)|9(?:0(?:00|51)0|12)|(?:11(?:4|8[02-46-9])|7\\d\\d|90[2-4])\\d\\d|(?:118|90)1(?:[02-9]\\d|1[013-9])', example_number='112', possible_length=(3, 4, 5, 6)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='2(?:2[02358]|33|4[01]|50|6[1-4])|32[13]|8(?:22|88)|912', example_number='220', possible_length=(3,)),
    sms_services=PhoneNumberDesc(national_number_pattern='7\\d{4}', example_number='70000', possible_length=(5,)),
    short_data=True)
