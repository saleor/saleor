"""Auto-generated file, do not edit by hand. SO metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_SO = PhoneMetadata(id='SO', country_code=252, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[346-9]\\d{8}|[12679]\\d{7}|(?:[1-4]\\d|59)\\d{5}|[1348]\\d{5}', possible_length=(6, 7, 8, 9)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:1\\d|2[0-79]|3[0-46-8]|4[0-7]|59)\\d{5}|(?:[134]\\d|8[125])\\d{4}', example_number='4012345', possible_length=(6, 7)),
    mobile=PhoneNumberDesc(national_number_pattern='28\\d{5}|(?:6[1-9]|79)\\d{6,7}|(?:15|24|(?:3[59]|4[89]|8[08])\\d|60|7[1-8]|9(?:0[67]|[2-9]))\\d{6}', example_number='71123456', possible_length=(7, 8, 9)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['8[125]']),
        NumberFormat(pattern='(\\d{6})', format='\\1', leading_digits_pattern=['[134]']),
        NumberFormat(pattern='(\\d)(\\d{6})', format='\\1 \\2', leading_digits_pattern=['1|2[0-79]|3[0-46-8]|4[0-7]|59']),
        NumberFormat(pattern='(\\d)(\\d{7})', format='\\1 \\2', leading_digits_pattern=['24|[67]']),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['[348]|64|79[0-8]|90']),
        NumberFormat(pattern='(\\d{2})(\\d{5,7})', format='\\1 \\2', leading_digits_pattern=['1|28|6[1-35-9]|799|9[2-9]'])])
