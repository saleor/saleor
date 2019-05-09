"""Auto-generated file, do not edit by hand. CR metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_CR = PhoneMetadata(id='CR', country_code=506, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:8\\d|90)\\d{8}|[24-8]\\d{7}', possible_length=(8, 10)),
    fixed_line=PhoneNumberDesc(national_number_pattern='210[7-9]\\d{4}|2(?:[024-7]\\d|1[1-9])\\d{5}', example_number='22123456', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='6500[01]\\d{3}|5(?:0[01]|7[0-3])\\d{5}|(?:6[0-4]|7[0-3]|8[3-9])\\d{6}', example_number='83123456', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='800\\d{7}', example_number='8001234567', possible_length=(10,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='90[059]\\d{7}', example_number='9001234567', possible_length=(10,)),
    voip=PhoneNumberDesc(national_number_pattern='(?:210[0-6]|4\\d{3}|5100)\\d{4}', example_number='40001234', possible_length=(8,)),
    national_prefix_for_parsing='(19(?:0[0-2468]|1[09]|20|66|77|99))',
    number_format=[NumberFormat(pattern='(\\d{4})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[24-7]|8[3-9]'], domestic_carrier_code_formatting_rule='$CC \\1'),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{4})', format='\\1-\\2-\\3', leading_digits_pattern=['[89]'], domestic_carrier_code_formatting_rule='$CC \\1')])
