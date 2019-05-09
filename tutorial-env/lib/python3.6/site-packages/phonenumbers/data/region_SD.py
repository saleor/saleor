"""Auto-generated file, do not edit by hand. SD metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_SD = PhoneMetadata(id='SD', country_code=249, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[19]\\d{8}', possible_length=(9,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='1(?:5[3-7]|8[35-7])\\d{6}', example_number='153123456', possible_length=(9,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:1[0-2]|9[0-3569])\\d{7}', example_number='911231234', possible_length=(9,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['[19]'], national_prefix_formatting_rule='0\\1')])
