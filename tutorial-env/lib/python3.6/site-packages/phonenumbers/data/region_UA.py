"""Auto-generated file, do not edit by hand. UA metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_UA = PhoneMetadata(id='UA', country_code=380, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[89]\\d{9}|[3-9]\\d{8}', possible_length=(9, 10), possible_length_local_only=(5, 6, 7)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:3[1-8]|4[13-8]|5[1-7]|6[12459])\\d{7}', example_number='311234567', possible_length=(9,), possible_length_local_only=(5, 6, 7)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:50|6[36-8]|7[1-3]|9[1-9])\\d{7}', example_number='501234567', possible_length=(9,)),
    toll_free=PhoneNumberDesc(national_number_pattern='800[1-8]\\d{5,6}', example_number='800123456', possible_length=(9, 10)),
    premium_rate=PhoneNumberDesc(national_number_pattern='900[239]\\d{5,6}', example_number='900212345', possible_length=(9, 10)),
    voip=PhoneNumberDesc(national_number_pattern='89[1-579]\\d{6}', example_number='891234567', possible_length=(9,)),
    preferred_international_prefix='0~0',
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['6[12][29]|(?:3[1-8]|4[136-8]|5[12457]|6[49])2|(?:56|65)[24]', '6[12][29]|(?:35|4[1378]|5[12457]|6[49])2|(?:56|65)[24]|(?:3[1-46-8]|46)2[013-9]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['4[45][0-5]|5(?:0|6[37])|6(?:[12][018]|[36-8])|7|89|9[1-9]|(?:48|57)[0137-9]', '4[45][0-5]|5(?:0|6(?:3[14-7]|7))|6(?:[12][018]|[36-8])|7|89|9[1-9]|(?:48|57)[0137-9]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{4})(\\d{5})', format='\\1 \\2', leading_digits_pattern=['[3-6]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3,4})', format='\\1 \\2 \\3', leading_digits_pattern=['[89]'], national_prefix_formatting_rule='0\\1')])
