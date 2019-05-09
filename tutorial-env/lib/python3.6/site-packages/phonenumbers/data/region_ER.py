"""Auto-generated file, do not edit by hand. ER metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_ER = PhoneMetadata(id='ER', country_code=291, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[178]\\d{6}', possible_length=(7,), possible_length_local_only=(6,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:1(?:1[12568]|[24]0|55|6[146])|8\\d\\d)\\d{4}', example_number='8370362', possible_length=(7,), possible_length_local_only=(6,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:17[1-3]|7\\d\\d)\\d{4}', example_number='7123456', possible_length=(7,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d)(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['[178]'], national_prefix_formatting_rule='0\\1')])
