"""Auto-generated file, do not edit by hand. LK metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_LK = PhoneMetadata(id='LK', country_code=94, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[1-7]\\d|[89]1)\\d{7}', possible_length=(9,), possible_length_local_only=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:[189]1|2[13-7]|3[1-8]|4[157]|5[12457]|6[35-7])[2-57]\\d{6}', example_number='112345678', possible_length=(9,), possible_length_local_only=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='7[0-25-8]\\d{7}', example_number='712345678', possible_length=(9,)),
    uan=PhoneNumberDesc(national_number_pattern='1973\\d{5}', example_number='197312345', possible_length=(9,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['7'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['[1-689]'], national_prefix_formatting_rule='0\\1')])
