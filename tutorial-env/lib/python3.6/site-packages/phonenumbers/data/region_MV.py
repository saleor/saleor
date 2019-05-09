"""Auto-generated file, do not edit by hand. MV metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_MV = PhoneMetadata(id='MV', country_code=960, international_prefix='0(?:0|19)',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:800|9[0-57-9]\\d)\\d{7}|[34679]\\d{6}', possible_length=(7, 10)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:3(?:0[0-3]|3[0-59])|6(?:[57][02468]|6[024-68]|8[024689]))\\d{4}', example_number='6701234', possible_length=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='46[46]\\d{4}|(?:7[2-9]|9[14-9])\\d{5}', example_number='7712345', possible_length=(7,)),
    toll_free=PhoneNumberDesc(national_number_pattern='800\\d{7}', example_number='8001234567', possible_length=(10,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='900\\d{7}', example_number='9001234567', possible_length=(10,)),
    uan=PhoneNumberDesc(national_number_pattern='4[05]0\\d{4}', example_number='4001234', possible_length=(7,)),
    preferred_international_prefix='00',
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1-\\2', leading_digits_pattern=['[3467]|9[14-9]']),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['[89]'])])
