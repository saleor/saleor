"""Auto-generated file, do not edit by hand. TR metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_TR = PhoneMetadata(id='TR', country_code=90, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[2-58]\\d\\d|900)\\d{7}|4\\d{6}', possible_length=(7, 10)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:2(?:[13][26]|[28][2468]|[45][268]|[67][246])|3(?:[13][28]|[24-6][2468]|[78][02468]|92)|4(?:[16][246]|[23578][2468]|4[26]))\\d{7}', example_number='2123456789', possible_length=(10,)),
    mobile=PhoneNumberDesc(national_number_pattern='56161\\d{5}|5(?:0[15-7]|1[06]|24|[34]\\d|5[1-59]|9[46])\\d{7}', example_number='5012345678', possible_length=(10,)),
    toll_free=PhoneNumberDesc(national_number_pattern='800\\d{7}', example_number='8001234567', possible_length=(10,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='(?:8[89]8|900)\\d{7}', example_number='9001234567', possible_length=(10,)),
    personal_number=PhoneNumberDesc(national_number_pattern='592(?:21[12]|461)\\d{4}', example_number='5922121234', possible_length=(10,)),
    pager=PhoneNumberDesc(national_number_pattern='512\\d{7}', example_number='5123456789', possible_length=(10,)),
    uan=PhoneNumberDesc(national_number_pattern='(?:444|850\\d{3})\\d{4}', example_number='4441444', possible_length=(7, 10)),
    no_international_dialling=PhoneNumberDesc(national_number_pattern='444\\d{4}', possible_length=(7,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{3})(\\d)(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['444'], national_prefix_optional_when_formatting=True),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['512|8[0589]|90'], national_prefix_formatting_rule='0\\1', national_prefix_optional_when_formatting=True),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['5(?:[0-59]|61)', '5(?:[0-59]|616)', '5(?:[0-59]|6161)'], national_prefix_formatting_rule='0\\1', national_prefix_optional_when_formatting=True),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[24][1-8]|3[1-9]'], national_prefix_formatting_rule='(0\\1)', national_prefix_optional_when_formatting=True)],
    intl_number_format=[NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['512|8[0589]|90']),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['5(?:[0-59]|61)', '5(?:[0-59]|616)', '5(?:[0-59]|6161)']),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[24][1-8]|3[1-9]'])],
    mobile_number_portable_region=True)
