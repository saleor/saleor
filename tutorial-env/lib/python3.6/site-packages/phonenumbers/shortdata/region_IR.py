"""Auto-generated file, do not edit by hand. IR metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_IR = PhoneMetadata(id='IR', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[129]\\d{2,5}', possible_length=(3, 4, 5, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:1[0-68]|2[0-59]|9[0-579])|911', example_number='110', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:1[025]|25)|911', example_number='110', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:1[0-68]|2[0-59]|3[346-8]|4(?:[0147]|[289]0)|5(?:0[14]|1[02479]|2[0-3]|39|[49]0|65)|6(?:[16]6|[27]|90)|8(?:03|1[18]|22|3[37]|4[28]|88|99)|9[0-579])|20(?:[09]0|1(?:[038]|1[079]|26|9[69])|2[01])|9(?:11|9(?:0009|90))', example_number='110', possible_length=(3, 4, 5, 6)),
    standard_rate=PhoneNumberDesc(national_number_pattern='1(?:5[0-469]|8[0-489])\\d', example_number='1500', possible_length=(4,)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='(?:1(?:5[0-469]|8[0-489])|99(?:0\\d\\d|9))\\d', example_number='1500', possible_length=(4, 6)),
    sms_services=PhoneNumberDesc(national_number_pattern='990\\d{3}', example_number='990000', possible_length=(6,)),
    short_data=True)
