"""Auto-generated file, do not edit by hand. HU metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_HU = PhoneMetadata(id='HU', country_code=36, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[2357]\\d{8}|[1-9]\\d{7}', possible_length=(8, 9), possible_length_local_only=(6, 7)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:1\\d|[27][2-9]|3[2-7]|4[24-9]|5[2-79]|6[23689]|8[2-57-9]|9[2-69])\\d{6}', example_number='12345678', possible_length=(8,), possible_length_local_only=(6, 7)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:[257]0|3[01])\\d{7}', example_number='201234567', possible_length=(9,)),
    toll_free=PhoneNumberDesc(national_number_pattern='[48]0\\d{6}', example_number='80123456', possible_length=(8,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='9[01]\\d{6}', example_number='90123456', possible_length=(8,)),
    voip=PhoneNumberDesc(national_number_pattern='21\\d{7}', example_number='211234567', possible_length=(9,)),
    uan=PhoneNumberDesc(national_number_pattern='38\\d{7}', example_number='381234567', possible_length=(9,)),
    no_international_dialling=PhoneNumberDesc(national_number_pattern='[48]0\\d{6}', possible_length=(8,)),
    national_prefix='06',
    national_prefix_for_parsing='06',
    number_format=[NumberFormat(pattern='(\\d)(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['1'], national_prefix_formatting_rule='(\\1)'),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{3,4})', format='\\1 \\2 \\3', leading_digits_pattern=['[2-9]'], national_prefix_formatting_rule='(\\1)')],
    mobile_number_portable_region=True)
