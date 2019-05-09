"""Auto-generated file, do not edit by hand. DM metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_DM = PhoneMetadata(id='DM', country_code=1, international_prefix='011',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[58]\\d\\d|767|900)\\d{7}', possible_length=(10,), possible_length_local_only=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='767(?:2(?:55|66)|4(?:2[01]|4[0-25-9])|50[0-4]|70[1-3])\\d{4}', example_number='7674201234', possible_length=(10,), possible_length_local_only=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='767(?:2(?:[2-4689]5|7[5-7])|31[5-7]|61[1-7])\\d{4}', example_number='7672251234', possible_length=(10,), possible_length_local_only=(7,)),
    toll_free=PhoneNumberDesc(national_number_pattern='8(?:00|33|44|55|66|77|88)[2-9]\\d{6}', example_number='8002123456', possible_length=(10,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='900[2-9]\\d{6}', example_number='9002123456', possible_length=(10,)),
    personal_number=PhoneNumberDesc(national_number_pattern='5(?:00|2[12]|33|44|66|77|88)[2-9]\\d{6}', example_number='5002345678', possible_length=(10,)),
    national_prefix='1',
    national_prefix_for_parsing='1|([2-7]\\d{6})$',
    national_prefix_transform_rule='767\\1',
    leading_digits='767')
