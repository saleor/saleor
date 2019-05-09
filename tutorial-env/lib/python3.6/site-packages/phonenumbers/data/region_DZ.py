"""Auto-generated file, do not edit by hand. DZ metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_DZ = PhoneMetadata(id='DZ', country_code=213, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[1-4]|[5-79]\\d|80)\\d{7}', possible_length=(8, 9)),
    fixed_line=PhoneNumberDesc(national_number_pattern='9619\\d{5}|(?:1\\d|2[013-79]|3[0-8]|4[0135689])\\d{6}', example_number='12345678', possible_length=(8, 9)),
    mobile=PhoneNumberDesc(national_number_pattern='67[0-6]\\d{6}|(?:5[4-6]|6[569]|7[7-9])\\d{7}', example_number='551234567', possible_length=(9,)),
    toll_free=PhoneNumberDesc(national_number_pattern='800\\d{6}', example_number='800123456', possible_length=(9,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='80[3-689]1\\d{5}', example_number='808123456', possible_length=(9,)),
    shared_cost=PhoneNumberDesc(national_number_pattern='80[12]1\\d{5}', example_number='801123456', possible_length=(9,)),
    voip=PhoneNumberDesc(national_number_pattern='98[23]\\d{6}', example_number='983123456', possible_length=(9,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[1-4]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['9'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{3})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[5-8]'], national_prefix_formatting_rule='0\\1')])
