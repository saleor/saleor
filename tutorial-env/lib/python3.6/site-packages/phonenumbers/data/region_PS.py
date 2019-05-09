"""Auto-generated file, do not edit by hand. PS metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_PS = PhoneMetadata(id='PS', country_code=970, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[2489]2\\d{6}|(?:1\\d|5)\\d{8}', possible_length=(8, 9, 10), possible_length_local_only=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:22[2-47-9]|42[45]|82[01458]|92[369])\\d{5}', example_number='22234567', possible_length=(8,), possible_length_local_only=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='5[69]\\d{7}', example_number='599123456', possible_length=(9,)),
    toll_free=PhoneNumberDesc(national_number_pattern='1800\\d{6}', example_number='1800123456', possible_length=(10,)),
    shared_cost=PhoneNumberDesc(national_number_pattern='1700\\d{6}', example_number='1700123456', possible_length=(10,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d)(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['[2489]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['5'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{4})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['1'])])
