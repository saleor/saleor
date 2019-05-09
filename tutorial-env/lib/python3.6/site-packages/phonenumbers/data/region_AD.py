"""Auto-generated file, do not edit by hand. AD metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_AD = PhoneMetadata(id='AD', country_code=376, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:1|6\\d)\\d{7}|[136-9]\\d{5}', possible_length=(6, 8, 9)),
    fixed_line=PhoneNumberDesc(national_number_pattern='[78]\\d{5}', example_number='712345', possible_length=(6,)),
    mobile=PhoneNumberDesc(national_number_pattern='690\\d{6}|[36]\\d{5}', example_number='312345', possible_length=(6, 9)),
    toll_free=PhoneNumberDesc(national_number_pattern='180[02]\\d{4}', example_number='18001234', possible_length=(8,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='[19]\\d{5}', example_number='912345', possible_length=(6,)),
    no_international_dialling=PhoneNumberDesc(national_number_pattern='1800\\d{4}', possible_length=(8,)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{3})', format='\\1 \\2', leading_digits_pattern=['[136-9]']),
        NumberFormat(pattern='(\\d{4})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['1']),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['6'])])
