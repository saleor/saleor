"""Auto-generated file, do not edit by hand. PM metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_PM = PhoneMetadata(id='PM', country_code=508, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[45]\\d{5}', possible_length=(6,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:4[1-3]|50)\\d{4}', example_number='430123', possible_length=(6,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:4[02-4]|5[05])\\d{4}', example_number='551234', possible_length=(6,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3', leading_digits_pattern=['[45]'], national_prefix_formatting_rule='0\\1')])
