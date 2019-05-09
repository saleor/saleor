"""Auto-generated file, do not edit by hand. EC metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_EC = PhoneMetadata(id='EC', country_code=593, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='1800\\d{6,7}|(?:[2-7]|9\\d)\\d{7}', possible_length=(8, 9, 10, 11), possible_length_local_only=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='[2-7][2-7]\\d{6}', example_number='22123456', possible_length=(8,), possible_length_local_only=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='964[0-2]\\d{5}|9(?:39|[57][89]|6[0-37-9]|[89]\\d)\\d{6}', example_number='991234567', possible_length=(9,)),
    toll_free=PhoneNumberDesc(national_number_pattern='1800\\d{6,7}', example_number='18001234567', possible_length=(10, 11)),
    voip=PhoneNumberDesc(national_number_pattern='[2-7]890\\d{4}', example_number='28901234', possible_length=(8,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1-\\2', leading_digits_pattern=['[2-7]']),
        NumberFormat(pattern='(\\d)(\\d{3})(\\d{4})', format='\\1 \\2-\\3', leading_digits_pattern=['[2-7]'], national_prefix_formatting_rule='(0\\1)'),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['9'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{4})(\\d{3})(\\d{3,4})', format='\\1 \\2 \\3', leading_digits_pattern=['1'])],
    intl_number_format=[NumberFormat(pattern='(\\d)(\\d{3})(\\d{4})', format='\\1-\\2-\\3', leading_digits_pattern=['[2-7]']),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['9']),
        NumberFormat(pattern='(\\d{4})(\\d{3})(\\d{3,4})', format='\\1 \\2 \\3', leading_digits_pattern=['1'])],
    mobile_number_portable_region=True)
