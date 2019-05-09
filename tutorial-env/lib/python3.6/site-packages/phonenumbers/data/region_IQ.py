"""Auto-generated file, do not edit by hand. IQ metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_IQ = PhoneMetadata(id='IQ', country_code=964, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:1|7\\d\\d)\\d{7}|[2-6]\\d{7,8}', possible_length=(8, 9, 10), possible_length_local_only=(6, 7)),
    fixed_line=PhoneNumberDesc(national_number_pattern='1\\d{7}|(?:2[13-5]|3[02367]|4[023]|5[03]|6[026])\\d{6,7}', example_number='12345678', possible_length=(8, 9), possible_length_local_only=(6, 7)),
    mobile=PhoneNumberDesc(national_number_pattern='7[3-9]\\d{8}', example_number='7912345678', possible_length=(10,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d)(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['1'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{3,4})', format='\\1 \\2 \\3', leading_digits_pattern=['[2-6]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['7'], national_prefix_formatting_rule='0\\1')])
