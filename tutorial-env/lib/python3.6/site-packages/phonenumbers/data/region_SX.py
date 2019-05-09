"""Auto-generated file, do not edit by hand. SX metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_SX = PhoneMetadata(id='SX', country_code=1, international_prefix='011',
    general_desc=PhoneNumberDesc(national_number_pattern='7215\\d{6}|(?:[58]\\d\\d|900)\\d{7}', possible_length=(10,), possible_length_local_only=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='7215(?:4[2-8]|8[239]|9[056])\\d{4}', example_number='7215425678', possible_length=(10,), possible_length_local_only=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='7215(?:1[02]|2\\d|5[034679]|8[014-8])\\d{4}', example_number='7215205678', possible_length=(10,), possible_length_local_only=(7,)),
    toll_free=PhoneNumberDesc(national_number_pattern='8(?:00|33|44|55|66|77|88)[2-9]\\d{6}', example_number='8002123456', possible_length=(10,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='900[2-9]\\d{6}', example_number='9002123456', possible_length=(10,)),
    personal_number=PhoneNumberDesc(national_number_pattern='5(?:00|2[12]|33|44|66|77|88)[2-9]\\d{6}', example_number='5002345678', possible_length=(10,)),
    national_prefix='1',
    national_prefix_for_parsing='1|(5\\d{6})$',
    national_prefix_transform_rule='721\\1',
    leading_digits='721')
