"""Auto-generated file, do not edit by hand. BJ metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_BJ = PhoneMetadata(id='BJ', country_code=229, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[2689]\\d{7}', possible_length=(8,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='2(?:02|1[037]|2[45]|3[68])\\d{5}', example_number='20211234', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:6\\d|9[03-9])\\d{6}', example_number='90011234', possible_length=(8,)),
    voip=PhoneNumberDesc(national_number_pattern='857[58]\\d{4}', example_number='85751234', possible_length=(8,)),
    uan=PhoneNumberDesc(national_number_pattern='81\\d{6}', example_number='81123456', possible_length=(8,)),
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[2689]'])])
