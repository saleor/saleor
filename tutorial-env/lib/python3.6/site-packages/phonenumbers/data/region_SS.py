"""Auto-generated file, do not edit by hand. SS metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_SS = PhoneMetadata(id='SS', country_code=211, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[19]\\d{8}', possible_length=(9,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='18\\d{7}', example_number='181234567', possible_length=(9,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:12|9[1257])\\d{7}', example_number='977123456', possible_length=(9,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['[19]'], national_prefix_formatting_rule='0\\1')])
