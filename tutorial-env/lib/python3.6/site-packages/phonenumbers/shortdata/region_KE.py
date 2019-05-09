"""Auto-generated file, do not edit by hand. KE metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_KE = PhoneMetadata(id='KE', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[1-9]\\d{2,4}', possible_length=(3, 4, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:1(?:[246]|9\\d)|5(?:01|2[127]|6[26]\\d))|999', example_number='112', possible_length=(3, 4, 5)),
    premium_rate=PhoneNumberDesc(national_number_pattern='909\\d\\d', example_number='90900', possible_length=(5,)),
    emergency=PhoneNumberDesc(national_number_pattern='11[24]|999', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:0(?:[07-9]|1[0-25]|400)|1(?:[024-6]|9[0-579])|2[1-3]|3[01]|4[14]|5(?:[01][01]|2[0-24-79]|33|4[05]|5[59]|6(?:00|29|6[67]))|(?:6[035]\\d|[78])\\d|9(?:[02-9]\\d\\d|19))|(?:(?:2[0-79]|[37][0-29]|4[0-4]|6[2357]|8\\d)\\d|5(?:[0-7]\\d|99))\\d\\d|9(?:09\\d\\d|99)|8988', example_number='100', possible_length=(3, 4, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='1(?:(?:04|6[35])\\d\\d|3[01]|4[14]|5(?:1\\d|2[25]))|(?:(?:2[0-79]|[37][0-29]|4[0-4]|6[2357]|8\\d)\\d|5(?:[0-7]\\d|99)|909)\\d\\d|898\\d', example_number='130', possible_length=(3, 4, 5)),
    sms_services=PhoneNumberDesc(national_number_pattern='1(?:(?:04|6[035])\\d\\d|4[14]|5(?:01|55|6[26]\\d))|40404|8988|909\\d\\d', example_number='141', possible_length=(3, 4, 5)),
    short_data=True)
