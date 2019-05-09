"""Auto-generated file, do not edit by hand. UG metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_UG = PhoneMetadata(id='UG', country_code=256, international_prefix='00[057]',
    general_desc=PhoneNumberDesc(national_number_pattern='800\\d{6}|(?:[29]0|[347]\\d)\\d{7}', possible_length=(9,), possible_length_local_only=(5, 6, 7)),
    fixed_line=PhoneNumberDesc(national_number_pattern='20(?:(?:240|30[0-4])\\d|6(?:00[0-2]|30[0-4]))\\d{3}|(?:20(?:[0147]\\d|[26][5-9]|3[2367]|5[0-4]|8[0-2])|[34]\\d{3})\\d{5}', example_number='312345678', possible_length=(9,), possible_length_local_only=(5, 6, 7)),
    mobile=PhoneNumberDesc(national_number_pattern='7260\\d{5}|7(?:[0157-9]\\d|2[03]|30|4[0-4])\\d{6}', example_number='712345678', possible_length=(9,)),
    toll_free=PhoneNumberDesc(national_number_pattern='800[1-3]\\d{5}', example_number='800123456', possible_length=(9,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='90[1-3]\\d{6}', example_number='901123456', possible_length=(9,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{4})(\\d{5})', format='\\1 \\2', leading_digits_pattern=['202', '2024'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{3})(\\d{6})', format='\\1 \\2', leading_digits_pattern=['[27-9]|4(?:6[45]|[7-9])'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{7})', format='\\1 \\2', leading_digits_pattern=['[34]'], national_prefix_formatting_rule='0\\1')])
