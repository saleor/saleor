"""Auto-generated file, do not edit by hand. MM metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_MM = PhoneMetadata(id='MM', country_code=95, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d{5,7}|95\\d{6}|(?:[4-7]|9[0-46-9])\\d{6,8}|(?:2|8\\d)\\d{5,8}', possible_length=(6, 7, 8, 9, 10), possible_length_local_only=(5,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:1(?:(?:2\\d|3[56]|[89][0-6])\\d|4(?:2[2-469]|39|46|6[25]|7[0-2])|6)|2(?:2(?:00|8[34])|4(?:0\\d|2[246]|39|46|62|7[0-2])|51\\d\\d)|4(?:2(?:2\\d\\d|48[0-2])|[34]20\\d)|6(?:0(?:[23]|88\\d)|(?:124|320|[56]2\\d)\\d|247[23]|4(?:2[04]\\d|47[23])|7(?:(?:3\\d|8[01459])\\d|4(?:39|60|7[01])))|8(?:[1-3]2\\d|5(?:2\\d|4[1-9]))\\d)\\d{4}|5(?:2(?:2\\d{5,6}|47[023]\\d{4})|(?:347[23]|42(?:1|86)|(?:522|820)\\d|7(?:20\\d|48[0-2])|9(?:20\\d|47[01]))\\d{4})|7(?:120\\d{4,5}|(?:425\\d|5(?:202|96\\d))\\d{4})|(?:(?:1[2-6]\\d|4(?:2[24-8]|356|[46][2-6]|5[35])|5(?:[27][2-8]|3[2-68]|4[25-8]|5[23]|6[2-4]|8[25-7]|9[2-7])|6(?:[19]20|42[03-6]|(?:52|7[45])\\d)|7(?:[04][25-8]|[15][235-7]|22|3[2-4]))\\d|8(?:[135]2\\d\\d|2(?:2\\d\\d|320)))\\d{3}|25\\d{5,6}|(?:2[2-9]|43[235-7]|6(?:1[2356]|[24][2-6]|3[256]|5[2-4]|6[2-8]|7[235-7]|8[245]|9[24])|8(?:1[235689]|2[2-8]|32|4[24-7]|5[245]|6[23]))\\d{4}|(?:4[35]|5[48]|63|7[0145]|8[13])470\\d{4}|(?:4[35]|5[48]|63|7[0145]|8[13])4\\d{4}', example_number='1234567', possible_length=(6, 7, 8, 9), possible_length_local_only=(5,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:17[01]|9(?:2(?:[0-4]|[56]\\d\\d)|(?:3(?:[0-36]|4\\d)|(?:6[89]|89)\\d|7(?:3|5[0-2]|[6-9]\\d))\\d|4(?:(?:[0245]\\d|[1379])\\d|88)|5[0-6]|9(?:[089]|[5-7]\\d\\d))\\d)\\d{4}|9[69]1\\d{6}|9[68]\\d{6}', example_number='92123456', possible_length=(7, 8, 9, 10)),
    toll_free=PhoneNumberDesc(national_number_pattern='80080(?:[01][1-9]|2\\d)\\d{3}', example_number='8008001234', possible_length=(10,)),
    voip=PhoneNumberDesc(national_number_pattern='1333\\d{4}|[12]468\\d{4}', example_number='13331234', possible_length=(8,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d)(\\d{2})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['16|2'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['[45]|6(?:0[23]|[1-689]|7[235-7])|7(?:[0-4]|5[2-7])|8[1-6]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d)(\\d{3})(\\d{3,4})', format='\\1 \\2 \\3', leading_digits_pattern=['[12]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{3,4})', format='\\1 \\2 \\3', leading_digits_pattern=['[4-7]|8[1-35]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d)(\\d{3})(\\d{4,6})', format='\\1 \\2 \\3', leading_digits_pattern=['9(?:2[0-4]|[35-9]|4[137-9])'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d)(\\d{4})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['2'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['8'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d)(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['92'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d)(\\d{5})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['9'], national_prefix_formatting_rule='0\\1')])
