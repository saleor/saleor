"""Auto-generated file, do not edit by hand. PG metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_PG = PhoneMetadata(id='PG', country_code=675, international_prefix='00|140[1-3]',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:180|[78]\\d{3})\\d{4}|(?:[2-589]\\d|64)\\d{5}', possible_length=(7, 8)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:64[1-9]|7730|85[02-46-9])\\d{4}|(?:3[0-2]|4[257]|5[34]|77[0-24]|9[78])\\d{5}', example_number='3123456', possible_length=(7, 8)),
    mobile=PhoneNumberDesc(national_number_pattern='775\\d{5}|(?:7[0-689]|81)\\d{6}', example_number='70123456', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='180\\d{4}', example_number='1801234', possible_length=(7,)),
    voip=PhoneNumberDesc(national_number_pattern='2(?:0[0-47]|7[568])\\d{4}', example_number='2751234', possible_length=(7,)),
    preferred_international_prefix='00',
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['18|[2-69]|85']),
        NumberFormat(pattern='(\\d{4})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[78]'])])
