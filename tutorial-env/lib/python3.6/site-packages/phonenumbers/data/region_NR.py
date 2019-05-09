"""Auto-generated file, do not edit by hand. NR metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_NR = PhoneMetadata(id='NR', country_code=674, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:444|55\\d|888)\\d{4}', possible_length=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:444|888)\\d{4}', example_number='4441234', possible_length=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='55[4-9]\\d{4}', example_number='5551234', possible_length=(7,)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[458]'])])
