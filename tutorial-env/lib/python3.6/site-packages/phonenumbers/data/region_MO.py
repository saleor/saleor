"""Auto-generated file, do not edit by hand. MO metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_MO = PhoneMetadata(id='MO', country_code=853, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:28|[68]\\d)\\d{6}', possible_length=(8,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:28[2-57-9]|8(?:11|[2-57-9]\\d))\\d{5}', example_number='28212345', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='6(?:[2356]\\d\\d|8(?:[02][5-9]|[1478]\\d|[356][0-4]))\\d{4}', example_number='66123456', possible_length=(8,)),
    number_format=[NumberFormat(pattern='(\\d{4})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[268]'])])
