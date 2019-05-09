"""Auto-generated file, do not edit by hand. BD metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_BD = PhoneMetadata(id='BD', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[1579]\\d{2,4}', possible_length=(3, 4, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='10[0-26]|[19]99', example_number='100', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='10[0-2]|[19]99', example_number='100', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:0(?:[0-369]|5[1-4]|7[0-4]|8[0-29])|1[16-9]|2(?:[134]|2[0-5])|3(?:1\\d?|6[3-6])|5[2-9])|5012|786|9594|[19]99|1(?:0(?:50|6\\d)|33|4(?:0|1\\d))\\d', example_number='100', possible_length=(3, 4, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='1(?:11|2[13])|(?:501|959)\\d|786', example_number='111', possible_length=(3, 4)),
    sms_services=PhoneNumberDesc(national_number_pattern='959\\d', example_number='9590', possible_length=(4,)),
    short_data=True)
