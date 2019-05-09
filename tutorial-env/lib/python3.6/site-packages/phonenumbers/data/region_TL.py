"""Auto-generated file, do not edit by hand. TL metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_TL = PhoneMetadata(id='TL', country_code=670, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='7\\d{7}|(?:[2-47]\\d|[89]0)\\d{5}', possible_length=(7, 8)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:2[1-5]|3[1-9]|4[1-4])\\d{5}', example_number='2112345', possible_length=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='7[3-8]\\d{6}', example_number='77212345', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='80\\d{5}', example_number='8012345', possible_length=(7,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='90\\d{5}', example_number='9012345', possible_length=(7,)),
    personal_number=PhoneNumberDesc(national_number_pattern='70\\d{5}', example_number='7012345', possible_length=(7,)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[2-489]|70']),
        NumberFormat(pattern='(\\d{4})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['7'])])
