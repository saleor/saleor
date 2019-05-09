"""Auto-generated file, do not edit by hand. TH metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_TH = PhoneMetadata(id='TH', country_code=66, international_prefix='00[1-9]',
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d{8,9}|(?:[2-57]|[689]\\d)\\d{7}', possible_length=(8, 9, 10)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:2\\d|3[2-9]|4[2-5]|5[2-6]|7[3-7])\\d{6}', example_number='21234567', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:14|6[1-6]|[89]\\d)\\d{7}', example_number='812345678', possible_length=(9,)),
    toll_free=PhoneNumberDesc(national_number_pattern='1800\\d{6}', example_number='1800123456', possible_length=(10,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='1900\\d{6}', example_number='1900123456', possible_length=(10,)),
    voip=PhoneNumberDesc(national_number_pattern='6[08]\\d{7}', example_number='601234567', possible_length=(9,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d)(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['2'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{3,4})', format='\\1 \\2 \\3', leading_digits_pattern=['14|[3-9]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{4})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['1'])],
    mobile_number_portable_region=True)
