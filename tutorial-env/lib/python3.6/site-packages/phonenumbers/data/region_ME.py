"""Auto-generated file, do not edit by hand. ME metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_ME = PhoneMetadata(id='ME', country_code=382, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:20|[3-79]\\d)\\d{6}|80\\d{6,7}', possible_length=(8, 9), possible_length_local_only=(6,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:20[2-8]|3(?:[0-2][2-7]|3[24-7])|4(?:0[2-467]|1[2467])|5(?:[01][2467]|2[2-467]))\\d{5}', example_number='30234567', possible_length=(8,), possible_length_local_only=(6,)),
    mobile=PhoneNumberDesc(national_number_pattern='6(?:00|3[024]|6[0-25]|[7-9]\\d)\\d{5}', example_number='67622901', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='80(?:[0-2578]|9\\d)\\d{5}', example_number='80080002', possible_length=(8, 9)),
    premium_rate=PhoneNumberDesc(national_number_pattern='9(?:4[1568]|5[178])\\d{5}', example_number='94515151', possible_length=(8,)),
    voip=PhoneNumberDesc(national_number_pattern='78[1-49]\\d{5}', example_number='78108780', possible_length=(8,)),
    uan=PhoneNumberDesc(national_number_pattern='77[1-9]\\d{5}', example_number='77273012', possible_length=(8,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{3,4})', format='\\1 \\2 \\3', leading_digits_pattern=['[2-9]'], national_prefix_formatting_rule='0\\1')])
