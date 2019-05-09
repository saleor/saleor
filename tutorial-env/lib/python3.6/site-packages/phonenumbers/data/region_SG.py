"""Auto-generated file, do not edit by hand. SG metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_SG = PhoneMetadata(id='SG', country_code=65, international_prefix='0[0-3]\\d',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:(?:1\\d|8)\\d\\d|7000)\\d{7}|[3689]\\d{7}', possible_length=(8, 10, 11)),
    fixed_line=PhoneNumberDesc(national_number_pattern='6[1-9]\\d{6}', example_number='61234567', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:8[1-8]|9[0-8])\\d{6}', example_number='81234567', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='(?:18|8)00\\d{7}', example_number='18001234567', possible_length=(10, 11)),
    premium_rate=PhoneNumberDesc(national_number_pattern='1900\\d{7}', example_number='19001234567', possible_length=(11,)),
    voip=PhoneNumberDesc(national_number_pattern='3[12]\\d{6}', example_number='31234567', possible_length=(8,)),
    uan=PhoneNumberDesc(national_number_pattern='7000\\d{7}', example_number='70001234567', possible_length=(11,)),
    number_format=[NumberFormat(pattern='(\\d{4,5})', format='\\1', leading_digits_pattern=['1[0135-7]|77']),
        NumberFormat(pattern='(\\d{4})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[369]|8[1-8]']),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['8']),
        NumberFormat(pattern='(\\d{4})(\\d{4})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['7']),
        NumberFormat(pattern='(\\d{4})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['1'])],
    intl_number_format=[NumberFormat(pattern='(\\d{4})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[369]|8[1-8]']),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['8']),
        NumberFormat(pattern='(\\d{4})(\\d{4})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['7']),
        NumberFormat(pattern='(\\d{4})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['1'])],
    mobile_number_portable_region=True)
