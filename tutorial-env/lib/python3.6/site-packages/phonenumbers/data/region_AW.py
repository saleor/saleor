"""Auto-generated file, do not edit by hand. AW metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_AW = PhoneMetadata(id='AW', country_code=297, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[25-79]\\d\\d|800)\\d{4}', possible_length=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='5(?:2\\d|8[1-9])\\d{4}', example_number='5212345', possible_length=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:290|5[69]\\d|6(?:[03]0|22|4[0-2]|[69]\\d)|7(?:[34]\\d|7[07])|9(?:6[45]|9[4-8]))\\d{4}', example_number='5601234', possible_length=(7,)),
    toll_free=PhoneNumberDesc(national_number_pattern='800\\d{4}', example_number='8001234', possible_length=(7,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='900\\d{4}', example_number='9001234', possible_length=(7,)),
    voip=PhoneNumberDesc(national_number_pattern='(?:28\\d|501)\\d{4}', example_number='5011234', possible_length=(7,)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[25-9]'])])
