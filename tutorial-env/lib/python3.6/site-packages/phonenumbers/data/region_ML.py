"""Auto-generated file, do not edit by hand. ML metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_ML = PhoneMetadata(id='ML', country_code=223, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[246-9]\\d|50)\\d{6}', possible_length=(8,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='2(?:07[0-8]|12[67])\\d{4}|(?:2(?:02|1[4-689])|4(?:0[0-4]|4[1-39]))\\d{5}', example_number='20212345', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='2(?:079|17\\d)\\d{4}|(?:50|[679]\\d|8[239])\\d{6}', example_number='65012345', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='80\\d{6}', example_number='80012345', possible_length=(8,)),
    no_international_dialling=PhoneNumberDesc(national_number_pattern='80\\d{6}', possible_length=(8,)),
    number_format=[NumberFormat(pattern='(\\d{4})', format='\\1', leading_digits_pattern=['67[057-9]|74[045]', '67(?:0[09]|[59]9|77|8[89])|74(?:0[02]|44|55)']),
        NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[24-9]'])],
    intl_number_format=[NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[24-9]'])])
