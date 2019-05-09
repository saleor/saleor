"""Auto-generated file, do not edit by hand. FM metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_FM = PhoneMetadata(id='FM', country_code=691, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[39]\\d{6}', possible_length=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:3[2357]0[1-9]|9[2-6]\\d\\d)\\d{3}', example_number='3201234', possible_length=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:3[2357]0[1-9]|9[2-7]\\d\\d)\\d{3}', example_number='3501234', possible_length=(7,)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[39]'])])
