"""Auto-generated file, do not edit by hand. TT metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_TT = PhoneMetadata(id='TT', country_code=1, international_prefix='011',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[58]\\d\\d|900)\\d{7}', possible_length=(10,), possible_length_local_only=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='868(?:2(?:01|1[89]|[23]\\d)|6(?:0[7-9]|1[02-8]|2[1-9]|[3-69]\\d|7[0-79])|82[124])\\d{4}', example_number='8682211234', possible_length=(10,), possible_length_local_only=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='868(?:2(?:6[6-9]|[7-9]\\d)|[37](?:0[1-9]|1[02-9]|[2-9]\\d)|4[6-9]\\d|6(?:20|78|8\\d))\\d{4}', example_number='8682911234', possible_length=(10,), possible_length_local_only=(7,)),
    toll_free=PhoneNumberDesc(national_number_pattern='8(?:00|33|44|55|66|77|88)[2-9]\\d{6}', example_number='8002345678', possible_length=(10,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='900[2-9]\\d{6}', example_number='9002345678', possible_length=(10,)),
    personal_number=PhoneNumberDesc(national_number_pattern='5(?:00|2[12]|33|44|66|77|88)[2-9]\\d{6}', example_number='5002345678', possible_length=(10,)),
    voicemail=PhoneNumberDesc(national_number_pattern='868619\\d{4}', example_number='8686191234', possible_length=(10,), possible_length_local_only=(7,)),
    national_prefix='1',
    national_prefix_for_parsing='1|([2-46-8]\\d{6})$',
    national_prefix_transform_rule='868\\1',
    leading_digits='868')
