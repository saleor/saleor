"""Auto-generated file, do not edit by hand. JO metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_JO = PhoneMetadata(id='JO', country_code=962, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='900\\d{5}|(?:(?:[268]|7\\d)\\d|32|53)\\d{6}', possible_length=(8, 9)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:2(?:6(?:2[0-35-9]|3[0-578]|4[24-7]|5[0-24-8]|[6-8][023]|9[0-3])|7(?:0[1-79]|10|2[014-7]|3[0-689]|4[019]|5[0-3578]))|32(?:0[1-69]|1[1-35-7]|2[024-7]|3\\d|4[0-3]|[57][023]|6[03])|53(?:0[0-3]|[13][023]|2[0-59]|49|5[0-35-9]|6[15]|7[45]|8[1-6]|9[0-36-9])|6(?:2(?:[05]0|22)|3(?:00|33)|4(?:0[0-25]|1[2-7]|2[0569]|[38][07-9]|4[025689]|6[0-589]|7\\d|9[0-2])|5(?:[01][056]|2[034]|3[0-57-9]|4[178]|5[0-69]|6[0-35-9]|7[1-379]|8[0-68]|9[0239]))|87(?:[029]0|7[08]))\\d{4}', example_number='62001234', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='7(?:55[0-49]|(?:7[025-9]|[89][0-25-9])\\d)\\d{5}', example_number='790123456', possible_length=(9,)),
    toll_free=PhoneNumberDesc(national_number_pattern='80\\d{6}', example_number='80012345', possible_length=(8,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='900\\d{5}', example_number='90012345', possible_length=(8,)),
    shared_cost=PhoneNumberDesc(national_number_pattern='85\\d{6}', example_number='85012345', possible_length=(8,)),
    personal_number=PhoneNumberDesc(national_number_pattern='70\\d{7}', example_number='700123456', possible_length=(9,)),
    pager=PhoneNumberDesc(national_number_pattern='74(?:66|77)\\d{5}', example_number='746612345', possible_length=(9,)),
    uan=PhoneNumberDesc(national_number_pattern='8(?:10|8\\d)\\d{5}', example_number='88101234', possible_length=(8,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d)(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['[2356]|87'], national_prefix_formatting_rule='(0\\1)'),
        NumberFormat(pattern='(\\d{3})(\\d{5,6})', format='\\1 \\2', leading_digits_pattern=['[89]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{7})', format='\\1 \\2', leading_digits_pattern=['70'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d)(\\d{4})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['7'], national_prefix_formatting_rule='0\\1')],
    mobile_number_portable_region=True)
