"""Auto-generated file, do not edit by hand. BA metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_BA = PhoneMetadata(id='BA', country_code=387, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='6\\d{8}|(?:[35689]\\d|49|70)\\d{6}', possible_length=(8, 9), possible_length_local_only=(6,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:3(?:[05-79][2-9]|1[4579]|[23][24-9]|4[2-4689]|8[2457-9])|49[2-579]|5(?:0[2-49]|[13][2-9]|[268][2-4679]|4[4689]|5[2-79]|7[2-69]|9[2-4689]))\\d{5}', example_number='30212345', possible_length=(8,), possible_length_local_only=(6,)),
    mobile=PhoneNumberDesc(national_number_pattern='6(?:0(?:3\\d|40)|[1-356]\\d|44[0-6]|71[137])\\d{5}', example_number='61123456', possible_length=(8, 9)),
    toll_free=PhoneNumberDesc(national_number_pattern='8[08]\\d{6}', example_number='80123456', possible_length=(8,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='9[0246]\\d{6}', example_number='90123456', possible_length=(8,)),
    shared_cost=PhoneNumberDesc(national_number_pattern='8[12]\\d{6}', example_number='82123456', possible_length=(8,)),
    uan=PhoneNumberDesc(national_number_pattern='70(?:3[0146]|[56]0)\\d{4}', example_number='70341234', possible_length=(8,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{3})', format='\\1-\\2', leading_digits_pattern=['[2-9]']),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['6[1-356]|[7-9]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{3})', format='\\1 \\2-\\3', leading_digits_pattern=['[3-5]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})(\\d{3})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['6'], national_prefix_formatting_rule='0\\1')],
    intl_number_format=[NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['6[1-356]|[7-9]']),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{3})', format='\\1 \\2-\\3', leading_digits_pattern=['[3-5]']),
        NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})(\\d{3})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['6'])],
    mobile_number_portable_region=True)
