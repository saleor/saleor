"""Auto-generated file, do not edit by hand. NI metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_NI = PhoneMetadata(id='NI', country_code=505, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:1800|[25-8]\\d{3})\\d{4}', possible_length=(8,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='2\\d{7}', example_number='21234567', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:5(?:5[0-7]|[78]\\d)|6(?:20|3[035]|4[045]|5[05]|77|8[1-9]|9[059])|(?:7[5-8]|8\\d)\\d)\\d{5}', example_number='81234567', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='1800\\d{4}', example_number='18001234', possible_length=(8,)),
    number_format=[NumberFormat(pattern='(\\d{4})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[125-8]'])])
