"""Auto-generated file, do not edit by hand. CZ metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_CZ = PhoneMetadata(id='CZ', country_code=420, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[2-578]\\d|60)\\d{7}|9\\d{8,11}', possible_length=(9, 10, 11, 12)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:2\\d|3[1257-9]|4[16-9]|5[13-9])\\d{7}', example_number='212345678', possible_length=(9,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:60[1-8]|7(?:0[2-5]|[2379]\\d))\\d{6}', example_number='601123456', possible_length=(9,)),
    toll_free=PhoneNumberDesc(national_number_pattern='800\\d{6}', example_number='800123456', possible_length=(9,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='9(?:0[05689]|76)\\d{6}', example_number='900123456', possible_length=(9,)),
    shared_cost=PhoneNumberDesc(national_number_pattern='8[134]\\d{7}', example_number='811234567', possible_length=(9,)),
    personal_number=PhoneNumberDesc(national_number_pattern='70[01]\\d{6}', example_number='700123456', possible_length=(9,)),
    voip=PhoneNumberDesc(national_number_pattern='9[17]0\\d{6}', example_number='910123456', possible_length=(9,)),
    uan=PhoneNumberDesc(national_number_pattern='9(?:5\\d|7[2-4])\\d{6}', example_number='972123456', possible_length=(9,)),
    voicemail=PhoneNumberDesc(national_number_pattern='9(?:3\\d{9}|6\\d{7,10})', example_number='93123456789', possible_length=(9, 10, 11, 12)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['[2-8]|9[015-7]']),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['9']),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['9'])],
    mobile_number_portable_region=True)
