"""Auto-generated file, do not edit by hand. LU metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_LU = PhoneMetadata(id='LU', country_code=352, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='35[013-9]\\d{4,8}|6\\d{8}|35\\d{2,4}|(?:[2457-9]\\d|3[0-46-9])\\d{2,9}', possible_length=(4, 5, 6, 7, 8, 9, 10, 11)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:35[013-9]|80[2-9]|90[89])\\d{1,8}|(?:2[2-9]|3[0-46-9]|[457]\\d|8[13-9]|9[2-579])\\d{2,9}', example_number='27123456', possible_length=(4, 5, 6, 7, 8, 9, 10, 11)),
    mobile=PhoneNumberDesc(national_number_pattern='6(?:[269][18]|5[158]|7[189]|81)\\d{6}', example_number='628123456', possible_length=(9,)),
    toll_free=PhoneNumberDesc(national_number_pattern='800\\d{5}', example_number='80012345', possible_length=(8,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='90[015]\\d{5}', example_number='90012345', possible_length=(8,)),
    shared_cost=PhoneNumberDesc(national_number_pattern='801\\d{5}', example_number='80112345', possible_length=(8,)),
    voip=PhoneNumberDesc(national_number_pattern='20(?:1\\d{5}|[2-689]\\d{1,7})', example_number='20201234', possible_length=(4, 5, 6, 7, 8, 9, 10)),
    national_prefix_for_parsing='(15(?:0[06]|1[12]|[35]5|4[04]|6[26]|77|88|99)\\d)',
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{3})', format='\\1 \\2', leading_digits_pattern=['2(?:0[2-689]|[2-9])|[3-57]|8(?:0[2-9]|[13-9])|9(?:0[89]|[2-579])'], domestic_carrier_code_formatting_rule='$CC \\1'),
        NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3', leading_digits_pattern=['2(?:0[2-689]|[2-9])|[3-57]|8(?:0[2-9]|[13-9])|9(?:0[89]|[2-579])'], domestic_carrier_code_formatting_rule='$CC \\1'),
        NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['20[2-689]'], domestic_carrier_code_formatting_rule='$CC \\1'),
        NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})(\\d{1,2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['2(?:[0367]|4[3-8])'], domestic_carrier_code_formatting_rule='$CC \\1'),
        NumberFormat(pattern='(\\d{3})(\\d{2})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['80[01]|90[015]'], domestic_carrier_code_formatting_rule='$CC \\1'),
        NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})(\\d{3})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['20'], domestic_carrier_code_formatting_rule='$CC \\1'),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['6'], domestic_carrier_code_formatting_rule='$CC \\1'),
        NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})(\\d{2})(\\d{1,2})', format='\\1 \\2 \\3 \\4 \\5', leading_digits_pattern=['2(?:[0367]|4[3-8])'], domestic_carrier_code_formatting_rule='$CC \\1'),
        NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})(\\d{1,5})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[3-57]|8[13-9]|9(?:0[89]|[2-579])|(?:2|80)[2-9]'], domestic_carrier_code_formatting_rule='$CC \\1')],
    mobile_number_portable_region=True)
