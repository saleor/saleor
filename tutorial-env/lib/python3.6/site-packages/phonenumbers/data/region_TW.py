"""Auto-generated file, do not edit by hand. TW metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_TW = PhoneMetadata(id='TW', country_code=886, international_prefix='0(?:0[25-79]|19)',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[24589]|7\\d)\\d{8}|[2-8]\\d{7}|2\\d{6}', possible_length=(7, 8, 9, 10)),
    fixed_line=PhoneNumberDesc(national_number_pattern='24\\d{6,7}|8(?:2(?:3\\d|66)|36[24-9])\\d{4}|(?:2[235-8]\\d|3[2-9]|4(?:[239]\\d|[78])|5[2-8]|6[235-79]|7[1-9]|8[7-9])\\d{6}', example_number='221234567', possible_length=(8, 9)),
    mobile=PhoneNumberDesc(national_number_pattern='9[0-8]\\d{7}', example_number='912345678', possible_length=(9,)),
    toll_free=PhoneNumberDesc(national_number_pattern='80[0-79]\\d{6}', example_number='800123456', possible_length=(9,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='20(?:[013-9]\\d\\d|2)\\d{4}', example_number='203123456', possible_length=(7, 9)),
    personal_number=PhoneNumberDesc(national_number_pattern='99\\d{7}', example_number='990123456', possible_length=(9,)),
    voip=PhoneNumberDesc(national_number_pattern='70\\d{8}', example_number='7012345678', possible_length=(10,)),
    uan=PhoneNumberDesc(national_number_pattern='50[0-46-9]\\d{6}', example_number='500123456', possible_length=(9,)),
    national_prefix='0',
    preferred_extn_prefix='#',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{2})(\\d)(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['202'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d)(\\d{3,4})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['[25][2-8]|[346]|7[1-9]|8[237-9]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['[258]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['9'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{4})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['7'], national_prefix_formatting_rule='0\\1')],
    mobile_number_portable_region=True)
