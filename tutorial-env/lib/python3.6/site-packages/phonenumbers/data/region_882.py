"""Auto-generated file, do not edit by hand. 882 metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_882 = PhoneMetadata(id='001', country_code=882, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d{6,11}|3\\d{6}(?:\\d{2,5})?', possible_length=(7, 8, 9, 10, 11, 12)),
    mobile=PhoneNumberDesc(national_number_pattern='3(?:37\\d\\d|42)\\d{4}|3(?:2|47|7\\d{3})\\d{7}', example_number='3421234', possible_length=(7, 9, 10, 12)),
    voip=PhoneNumberDesc(national_number_pattern='1(?:3(?:0[0347]|[13][0139]|2[035]|4[013568]|6[0459]|7[06]|8[15-8]|9[0689])\\d{4}|6\\d{5,10})|3(?:45|9\\d{3})\\d{7}', example_number='390123456789', possible_length=(7, 8, 9, 10, 11, 12)),
    voicemail=PhoneNumberDesc(national_number_pattern='348[57]\\d{7}', example_number='34851234567', possible_length=(11,)),
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{5})', format='\\1 \\2', leading_digits_pattern=['16|342']),
        NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['1']),
        NumberFormat(pattern='(\\d{2})(\\d{4})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['3[23]']),
        NumberFormat(pattern='(\\d{2})(\\d{3,4})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['1']),
        NumberFormat(pattern='(\\d{2})(\\d{4})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['34[57]']),
        NumberFormat(pattern='(\\d{3})(\\d{4})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['34']),
        NumberFormat(pattern='(\\d{2})(\\d{4,5})(\\d{5})', format='\\1 \\2 \\3', leading_digits_pattern=['[13]'])])
