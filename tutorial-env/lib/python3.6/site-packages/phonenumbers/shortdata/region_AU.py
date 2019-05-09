"""Auto-generated file, do not edit by hand. AU metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_AU = PhoneMetadata(id='AU', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[0-27]\\d{2,7}', possible_length=(3, 4, 5, 6, 7, 8)),
    toll_free=PhoneNumberDesc(national_number_pattern='000|1(?:06|12|258885|55\\d)|733', example_number='000', possible_length=(3, 4, 7)),
    premium_rate=PhoneNumberDesc(national_number_pattern='1(?:2(?:34|456)|9\\d{4,6})', example_number='1234', possible_length=(4, 5, 6, 7, 8)),
    emergency=PhoneNumberDesc(national_number_pattern='000|1(?:06|12)', example_number='000', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='000|1(?:06|1(?:00|2|9[46])|2(?:[23]\\d|(?:4|5\\d)\\d{2,3}|8(?:[013-9]\\d|2))|555|9\\d{4,6})|225|7(?:33|67)', example_number='000', possible_length=(3, 4, 5, 6, 7, 8)),
    standard_rate=PhoneNumberDesc(national_number_pattern='1(?:1[09]\\d|24733)|225|767', example_number='225', possible_length=(3, 4, 6)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='1(?:258885|55\\d)', example_number='1550', possible_length=(4, 7)),
    sms_services=PhoneNumberDesc(national_number_pattern='19\\d{4,6}', example_number='190000', possible_length=(6, 7, 8)),
    short_data=True)
