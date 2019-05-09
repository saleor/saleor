"""Auto-generated file, do not edit by hand. SC metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_SC = PhoneMetadata(id='SC', country_code=248, international_prefix='010|0[0-2]',
    general_desc=PhoneNumberDesc(national_number_pattern='8000\\d{3}|(?:[249]\\d|64)\\d{5}', possible_length=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='4[2-46]\\d{5}', example_number='4217123', possible_length=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='2[5-8]\\d{5}', example_number='2510123', possible_length=(7,)),
    toll_free=PhoneNumberDesc(national_number_pattern='8000\\d{3}', example_number='8000000', possible_length=(7,)),
    voip=PhoneNumberDesc(national_number_pattern='971\\d{4}|(?:64|95)\\d{5}', example_number='6412345', possible_length=(7,)),
    preferred_international_prefix='00',
    number_format=[NumberFormat(pattern='(\\d)(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['[246]'])])
