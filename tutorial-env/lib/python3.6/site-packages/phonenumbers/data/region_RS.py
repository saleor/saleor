"""Auto-generated file, do not edit by hand. RS metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_RS = PhoneMetadata(id='RS', country_code=381, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='38[02-9]\\d{6,9}|6\\d{7,9}|90\\d{4,8}|38\\d{5,6}|(?:7\\d\\d|800)\\d{3,9}|(?:[12]\\d|3[0-79])\\d{5,10}', possible_length=(6, 7, 8, 9, 10, 11, 12), possible_length_local_only=(4, 5, 6)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:11[1-9]\\d|(?:2[389]|39)(?:0[2-9]|[2-9]\\d))\\d{3,8}|(?:1[02-9]|2[0-24-7]|3[0-8])[2-9]\\d{4,9}', example_number='10234567', possible_length=(7, 8, 9, 10, 11, 12), possible_length_local_only=(4, 5, 6)),
    mobile=PhoneNumberDesc(national_number_pattern='6(?:[0-689]|7\\d)\\d{6,7}', example_number='601234567', possible_length=(8, 9, 10)),
    toll_free=PhoneNumberDesc(national_number_pattern='800\\d{3,9}', example_number='80012345', possible_length=(6, 7, 8, 9, 10, 11, 12)),
    premium_rate=PhoneNumberDesc(national_number_pattern='(?:78\\d|90[0169])\\d{3,7}', example_number='90012345', possible_length=(6, 7, 8, 9, 10)),
    uan=PhoneNumberDesc(national_number_pattern='7[06]\\d{4,10}', example_number='700123456', possible_length=(6, 7, 8, 9, 10, 11, 12)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{3,9})', format='\\1 \\2', leading_digits_pattern=['(?:2[389]|39)0|[7-9]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{5,10})', format='\\1 \\2', leading_digits_pattern=['[1-36]'], national_prefix_formatting_rule='0\\1')],
    mobile_number_portable_region=True)
