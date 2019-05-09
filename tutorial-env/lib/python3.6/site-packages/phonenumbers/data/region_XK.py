"""Auto-generated file, do not edit by hand. XK metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_XK = PhoneMetadata(id='XK', country_code=383, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[23]\\d{7,8}|(?:4\\d\\d|[89]00)\\d{5}', possible_length=(8, 9)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:2[89]|39)0\\d{6}|[23][89]\\d{6}', example_number='28012345', possible_length=(8, 9)),
    mobile=PhoneNumberDesc(national_number_pattern='4[3-79]\\d{6}', example_number='43201234', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='800\\d{5}', example_number='80001234', possible_length=(8,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='900\\d{5}', example_number='90001234', possible_length=(8,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{5})', format='\\1 \\2', leading_digits_pattern=['[89]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['[2-4]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['[23]'], national_prefix_formatting_rule='0\\1')])
