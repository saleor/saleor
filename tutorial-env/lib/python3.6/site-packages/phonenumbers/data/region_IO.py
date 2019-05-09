"""Auto-generated file, do not edit by hand. IO metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_IO = PhoneMetadata(id='IO', country_code=246, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='3\\d{6}', possible_length=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='37\\d{5}', example_number='3709100', possible_length=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='38\\d{5}', example_number='3801234', possible_length=(7,)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['3'])])
