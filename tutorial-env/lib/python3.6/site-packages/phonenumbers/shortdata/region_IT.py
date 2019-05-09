"""Auto-generated file, do not edit by hand. IT metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_IT = PhoneMetadata(id='IT', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[14]\\d{2,6}', possible_length=(3, 4, 5, 6, 7)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:1(?:[2358]|6\\d{3})|87)', example_number='112', possible_length=(3, 6)),
    premium_rate=PhoneNumberDesc(national_number_pattern='(?:12|4(?:[478](?:[0-4]|[5-9]\\d\\d)|55))\\d\\d', example_number='1200', possible_length=(4, 5, 7)),
    emergency=PhoneNumberDesc(national_number_pattern='11[2358]', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:0\\d{2,3}|1(?:[2-57-9]|6(?:000|111))|3[39]|4(?:82|9\\d{1,3})|5(?:00|1[58]|2[25]|3[03]|44|[59])|60|8[67]|9(?:[01]|2[2-9]|4\\d|696))|4(?:2323|5045)|(?:1(?:2|92[01])|4(?:3(?:[01]|[45]\\d\\d)|[478](?:[0-4]|[5-9]\\d\\d)|55))\\d\\d', example_number='112', possible_length=(3, 4, 5, 6, 7)),
    sms_services=PhoneNumberDesc(national_number_pattern='4(?:3(?:[01]|[45]\\d\\d)|[478](?:[0-4]|[5-9]\\d\\d)|5[05])\\d\\d', example_number='43000', possible_length=(5, 7)),
    short_data=True)
