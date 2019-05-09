"""Auto-generated file, do not edit by hand. IR metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_IR = PhoneMetadata(id='IR', country_code=98, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[1-9]\\d{9}|(?:[1-8]\\d\\d|9)\\d{3,4}', possible_length=(4, 5, 6, 7, 10), possible_length_local_only=(4, 5, 8)),
    fixed_line=PhoneNumberDesc(national_number_pattern='944111\\d{4}|94(?:(?:00|44)0|(?:11|2\\d)\\d|30[01])\\d{5}|(?:1[137]|2[13-68]|3[1458]|4[145]|5[1468]|6[16]|7[1467]|8[13467])(?:[03-57]\\d{7}|[16]\\d{3}(?:\\d{4})?|[289]\\d{3}(?:\\d(?:\\d{3})?)?)', example_number='2123456789', possible_length=(6, 7, 10), possible_length_local_only=(4, 5, 8)),
    mobile=PhoneNumberDesc(national_number_pattern='9(?:(?:0(?:[1-35]\\d|44)|(?:[13]\\d|2[0-2])\\d)\\d|9(?:(?:[0-2]\\d|44)\\d|510|8(?:1\\d|88)|9(?:0[013]|1[0134]|21|77|9[6-9])))\\d{5}', example_number='9123456789', possible_length=(10,)),
    voip=PhoneNumberDesc(national_number_pattern='993\\d{7}', example_number='9932123456', possible_length=(10,)),
    uan=PhoneNumberDesc(national_number_pattern='96(?:0[12]|2[16-8]|3(?:08|[14]5|[23]|66)|4(?:0|80)|5[01]|6[89]|86|9[19])', example_number='9601', possible_length=(4, 5)),
    no_international_dialling=PhoneNumberDesc(national_number_pattern='96(?:0[12]|2[16-8]|3(?:08|[14]5|[23]|66)|4(?:0|80)|5[01]|6[89]|86|9[19])|94(?:11[1-7]|440)\\d{5}', possible_length=(4, 5, 10)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{4,5})', format='\\1', leading_digits_pattern=['96'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{4,5})', format='\\1 \\2', leading_digits_pattern=['(?:1[137]|2[13-68]|3[1458]|4[145]|5[1468]|6[16]|7[1467]|8[13467])[12689]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3,4})', format='\\1 \\2 \\3', leading_digits_pattern=['9'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{4})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['[1-8]'], national_prefix_formatting_rule='0\\1')])
