"""Auto-generated file, do not edit by hand. BI metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_BI = PhoneMetadata(id='BI', country_code=257, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[267]\\d|31)\\d{6}', possible_length=(8,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='22\\d{6}', example_number='22201234', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:29|31|6[189]|7[125-9])\\d{6}', example_number='79561234', possible_length=(8,)),
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[2367]'])])
