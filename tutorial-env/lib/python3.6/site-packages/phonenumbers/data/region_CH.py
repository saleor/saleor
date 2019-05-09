"""Auto-generated file, do not edit by hand. CH metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_CH = PhoneMetadata(id='CH', country_code=41, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='8\\d{11}|[2-9]\\d{8}', possible_length=(9, 12)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:2[12467]|3[1-4]|4[134]|5[256]|6[12]|[7-9]1)\\d{7}', example_number='212345678', possible_length=(9,)),
    mobile=PhoneNumberDesc(national_number_pattern='7[35-9]\\d{7}', example_number='781234567', possible_length=(9,)),
    toll_free=PhoneNumberDesc(national_number_pattern='800\\d{6}', example_number='800123456', possible_length=(9,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='90[016]\\d{6}', example_number='900123456', possible_length=(9,)),
    shared_cost=PhoneNumberDesc(national_number_pattern='84[0248]\\d{6}', example_number='840123456', possible_length=(9,)),
    personal_number=PhoneNumberDesc(national_number_pattern='878\\d{6}', example_number='878123456', possible_length=(9,)),
    pager=PhoneNumberDesc(national_number_pattern='74[0248]\\d{6}', example_number='740123456', possible_length=(9,)),
    uan=PhoneNumberDesc(national_number_pattern='5[18]\\d{7}', example_number='581234567', possible_length=(9,)),
    voicemail=PhoneNumberDesc(national_number_pattern='860\\d{9}', example_number='860123456789', possible_length=(12,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['8[047]|90'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[2-79]|81'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{3})(\\d{2})(\\d{3})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4 \\5', leading_digits_pattern=['8'], national_prefix_formatting_rule='0\\1')],
    mobile_number_portable_region=True)
