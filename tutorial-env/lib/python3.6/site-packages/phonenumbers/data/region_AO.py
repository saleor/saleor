"""Auto-generated file, do not edit by hand. AO metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_AO = PhoneMetadata(id='AO', country_code=244, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[29]\\d{8}', possible_length=(9,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='2\\d(?:[0134][25-9]|[25-9]\\d)\\d{5}', example_number='222123456', possible_length=(9,)),
    mobile=PhoneNumberDesc(national_number_pattern='9[1-49]\\d{7}', example_number='923123456', possible_length=(9,)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['[29]'])])
