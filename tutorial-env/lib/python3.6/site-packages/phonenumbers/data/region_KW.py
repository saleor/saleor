"""Auto-generated file, do not edit by hand. KW metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_KW = PhoneMetadata(id='KW', country_code=965, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:18|[2569]\\d\\d)\\d{5}', possible_length=(7, 8)),
    fixed_line=PhoneNumberDesc(national_number_pattern='2(?:[23]\\d\\d|4(?:[1-35-9]\\d|44)|5(?:0[034]|[2-46]\\d|5[1-3]|7[1-7]))\\d{4}', example_number='22345678', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:52(?:22|5[25])|6(?:222|70[013-9]|93[039])|9(?:11[01]|702))\\d{4}|(?:5(?:[05]\\d|1[0-7]|6[56])|6(?:0[034679]|5[015-9]|6\\d|7[67]|9[069])|9(?:0[09]|22|4[01479]|55|6[0679]|7[1-9]|8[057-9]|9\\d))\\d{5}', example_number='50012345', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='18\\d{5}', example_number='1801234', possible_length=(7,)),
    number_format=[NumberFormat(pattern='(\\d{4})(\\d{3,4})', format='\\1 \\2', leading_digits_pattern=['[169]|2(?:[235]|4[1-35-9])|52']),
        NumberFormat(pattern='(\\d{3})(\\d{5})', format='\\1 \\2', leading_digits_pattern=['[25]'])],
    mobile_number_portable_region=True)
