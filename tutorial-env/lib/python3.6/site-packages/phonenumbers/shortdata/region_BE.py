"""Auto-generated file, do not edit by hand. BE metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_BE = PhoneMetadata(id='BE', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[1-9]\\d\\d(?:\\d(?:\\d{2})?)?', possible_length=(3, 4, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:0[0-25-8]|1[02]|7(?:12|77)|813)|(?:116|8)\\d{3}', example_number='100', possible_length=(3, 4, 6)),
    premium_rate=PhoneNumberDesc(national_number_pattern='1(?:2[03]|40)4|(?:1(?:[24]1|3[01])|[2-79]\\d\\d)\\d', example_number='1204', possible_length=(4,)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:0[01]|12)', example_number='100', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:0[0-8]|1(?:[027]|6117)|2(?:12|3[0-24])|313|414|5(?:1[05]|5[15]|66|95)|6(?:1[167]|36|6[16])|7(?:0[07]|1[27-9]|22|33|65|7[017])|81[39])|[2-9]\\d{3}|1(?:1600|45)0|1(?:[2-4]9|78)9|1[2-4]0[47]', example_number='100', possible_length=(3, 4, 6)),
    sms_services=PhoneNumberDesc(national_number_pattern='[2-9]\\d{3}', example_number='2000', possible_length=(4,)),
    short_data=True)
