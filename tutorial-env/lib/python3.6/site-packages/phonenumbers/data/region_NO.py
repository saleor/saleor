"""Auto-generated file, do not edit by hand. NO metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_NO = PhoneMetadata(id='NO', country_code=47, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:0|[2-9]\\d{3})\\d{4}', possible_length=(5, 8)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:2[1-4]|3[1-3578]|5[1-35-7]|6[1-4679]|7[0-8])\\d{6}', example_number='21234567', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:4[015-8]|5[89]|9\\d)\\d{6}', example_number='40612345', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='80[01]\\d{5}', example_number='80012345', possible_length=(8,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='82[09]\\d{5}', example_number='82012345', possible_length=(8,)),
    shared_cost=PhoneNumberDesc(national_number_pattern='810(?:0[0-6]|[2-8]\\d)\\d{3}', example_number='81021234', possible_length=(8,)),
    personal_number=PhoneNumberDesc(national_number_pattern='880\\d{5}', example_number='88012345', possible_length=(8,)),
    voip=PhoneNumberDesc(national_number_pattern='85[0-5]\\d{5}', example_number='85012345', possible_length=(8,)),
    uan=PhoneNumberDesc(national_number_pattern='(?:0[2-9]|81(?:0(?:0[7-9]|1\\d)|5\\d\\d))\\d{3}', example_number='02000', possible_length=(5, 8)),
    voicemail=PhoneNumberDesc(national_number_pattern='81[23]\\d{5}', example_number='81212345', possible_length=(8,)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{2})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['[489]']),
        NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[235-7]'])],
    main_country_for_code=True,
    leading_digits='[02-689]|7[0-8]',
    mobile_number_portable_region=True)
