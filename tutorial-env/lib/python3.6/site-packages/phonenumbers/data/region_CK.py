"""Auto-generated file, do not edit by hand. CK metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_CK = PhoneMetadata(id='CK', country_code=682, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[2-8]\\d{4}', possible_length=(5,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:2\\d|3[13-7]|4[1-5])\\d{3}', example_number='21234', possible_length=(5,)),
    mobile=PhoneNumberDesc(national_number_pattern='[5-8]\\d{4}', example_number='71234', possible_length=(5,)),
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{3})', format='\\1 \\2', leading_digits_pattern=['[2-8]'])])
