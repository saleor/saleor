"""Auto-generated file, do not edit by hand. EE metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_EE = PhoneMetadata(id='EE', country_code=372, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='8\\d{9}|[4578]\\d{7}|(?:[3-8]\\d\\d|900)\\d{4}', possible_length=(7, 8, 10)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:3[23589]|4[3-8]|6\\d|7[1-9]|88)\\d{5}', example_number='3212345', possible_length=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:5\\d|8[1-4])\\d{6}|5(?:(?:[02]\\d|5[0-478])\\d|1(?:[0-8]\\d|95)|6(?:4[0-4]|5[1-589]))\\d{3}', example_number='51234567', possible_length=(7, 8)),
    toll_free=PhoneNumberDesc(national_number_pattern='800(?:(?:0\\d\\d|1)\\d|[2-9])\\d{3}', example_number='80012345', possible_length=(7, 8, 10)),
    premium_rate=PhoneNumberDesc(national_number_pattern='(?:40\\d\\d|900)\\d{4}', example_number='9001234', possible_length=(7, 8)),
    personal_number=PhoneNumberDesc(national_number_pattern='70[0-2]\\d{5}', example_number='70012345', possible_length=(8,)),
    no_international_dialling=PhoneNumberDesc(national_number_pattern='800[2-9]\\d{3}', possible_length=(7,)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[369]|4[3-8]|5(?:[0-2]|5[0-478]|6[45])|7[1-9]', '[369]|4[3-8]|5(?:[02]|1(?:[0-8]|95)|5[0-478]|6(?:4[0-4]|5[1-589]))|7[1-9]']),
        NumberFormat(pattern='(\\d{4})(\\d{3,4})', format='\\1 \\2', leading_digits_pattern=['[45]|8(?:00|[1-4])', '[45]|8(?:00[1-9]|[1-4])']),
        NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['7']),
        NumberFormat(pattern='(\\d{4})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['80'])],
    mobile_number_portable_region=True)
