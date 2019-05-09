"""Auto-generated file, do not edit by hand. YE metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_YE = PhoneMetadata(id='YE', country_code=967, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:1|7\\d)\\d{7}|[1-7]\\d{6}', possible_length=(7, 8, 9), possible_length_local_only=(6,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='17\\d{6}|(?:[12][2-68]|3[2358]|4[2-58]|5[2-6]|6[3-58]|7[24-68])\\d{5}', example_number='1234567', possible_length=(7, 8), possible_length_local_only=(6,)),
    mobile=PhoneNumberDesc(national_number_pattern='7[0137]\\d{7}', example_number='712345678', possible_length=(9,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d)(\\d{3})(\\d{3,4})', format='\\1 \\2 \\3', leading_digits_pattern=['[1-6]|7[24-68]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['7'], national_prefix_formatting_rule='0\\1')])
