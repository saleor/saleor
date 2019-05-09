"""Auto-generated file, do not edit by hand. SY metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_SY = PhoneMetadata(id='SY', country_code=963, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[1-39]\\d{8}|[1-5]\\d{7}', possible_length=(8, 9), possible_length_local_only=(6, 7)),
    fixed_line=PhoneNumberDesc(national_number_pattern='[12]1\\d{6,7}|(?:1(?:[2356]|4\\d)|2[235]|3(?:[13]\\d|4)|4[13]|5[1-3])\\d{6}', example_number='112345678', possible_length=(8, 9), possible_length_local_only=(6, 7)),
    mobile=PhoneNumberDesc(national_number_pattern='9(?:22|[3-589]\\d|6[024-9])\\d{6}', example_number='944567890', possible_length=(9,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{3,4})', format='\\1 \\2 \\3', leading_digits_pattern=['[1-5]'], national_prefix_formatting_rule='0\\1', national_prefix_optional_when_formatting=True),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['9'], national_prefix_formatting_rule='0\\1', national_prefix_optional_when_formatting=True)])
