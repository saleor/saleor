"""Auto-generated file, do not edit by hand. GT metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_GT = PhoneMetadata(id='GT', country_code=502, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:1\\d{3}|[2-7])\\d{7}', possible_length=(8, 11)),
    fixed_line=PhoneNumberDesc(national_number_pattern='[267][2-9]\\d{6}', example_number='22456789', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='[3-5]\\d{7}', example_number='51234567', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='18[01]\\d{8}', example_number='18001112222', possible_length=(11,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='19\\d{9}', example_number='19001112222', possible_length=(11,)),
    number_format=[NumberFormat(pattern='(\\d{4})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[2-7]']),
        NumberFormat(pattern='(\\d{4})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['1'])])
