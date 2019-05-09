"""Auto-generated file, do not edit by hand. TZ metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_TZ = PhoneMetadata(id='TZ', country_code=255, international_prefix='00[056]',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[26-8]\\d|41|90)\\d{7}', possible_length=(9,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='2[2-8]\\d{7}', example_number='222345678', possible_length=(9,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:6[2-9]|7[13-9])\\d{7}', example_number='621234567', possible_length=(9,)),
    toll_free=PhoneNumberDesc(national_number_pattern='80[08]\\d{6}', example_number='800123456', possible_length=(9,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='90\\d{7}', example_number='900123456', possible_length=(9,)),
    shared_cost=PhoneNumberDesc(national_number_pattern='8(?:40|6[01])\\d{6}', example_number='840123456', possible_length=(9,)),
    voip=PhoneNumberDesc(national_number_pattern='41\\d{7}', example_number='412345678', possible_length=(9,)),
    no_international_dialling=PhoneNumberDesc(national_number_pattern='(?:8(?:[04]0|6[01])|90\\d)\\d{6}', possible_length=(9,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{2})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['[89]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['[24]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['[67]'], national_prefix_formatting_rule='0\\1')])
