"""Auto-generated file, do not edit by hand. SM metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_SM = PhoneMetadata(id='SM', country_code=378, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:0549|[5-7]\\d)\\d{6}', possible_length=(8, 10), possible_length_local_only=(6,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='0549(?:8[0157-9]|9\\d)\\d{4}', example_number='0549886377', possible_length=(10,), possible_length_local_only=(6,)),
    mobile=PhoneNumberDesc(national_number_pattern='6[16]\\d{6}', example_number='66661212', possible_length=(8,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='7[178]\\d{6}', example_number='71123456', possible_length=(8,)),
    voip=PhoneNumberDesc(national_number_pattern='5[158]\\d{6}', example_number='58001110', possible_length=(8,)),
    national_prefix_for_parsing='([89]\\d{5})$',
    national_prefix_transform_rule='0549\\1',
    number_format=[NumberFormat(pattern='(\\d{6})', format='\\1', leading_digits_pattern=['[89]']),
        NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[5-7]']),
        NumberFormat(pattern='(\\d{4})(\\d{6})', format='\\1 \\2', leading_digits_pattern=['0'])],
    intl_number_format=[NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[5-7]']),
        NumberFormat(pattern='(\\d{4})(\\d{6})', format='\\1 \\2', leading_digits_pattern=['0'])])
