"""Auto-generated file, do not edit by hand. GI metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_GI = PhoneMetadata(id='GI', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[158]\\d{2,5}', possible_length=(3, 4, 5, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:00|1[25]|23|4(?:1|7\\d)|5[15]|9[02-49])|555|(?:116\\d|80)\\d\\d', example_number='100', possible_length=(3, 4, 6)),
    premium_rate=PhoneNumberDesc(national_number_pattern='8[1-69]\\d\\d', example_number='8100', possible_length=(4,)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:12|9[09])', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:00|1(?:[25]|6(?:00[06]|1(?:1[17]|23))|8\\d\\d)|23|4(?:1|7[014])|5[015]|9[02-49])|555|8[0-79]\\d\\d|8(?:00|4[0-2]|8[0-589])', example_number='100', possible_length=(3, 4, 5, 6)),
    standard_rate=PhoneNumberDesc(national_number_pattern='150|87\\d\\d', example_number='150', possible_length=(3, 4)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='1(?:00|1(?:5|8\\d\\d)|23|51|9[2-4])|555|8(?:00|4[0-2]|8[0-589])', example_number='100', possible_length=(3, 5)),
    short_data=True)
