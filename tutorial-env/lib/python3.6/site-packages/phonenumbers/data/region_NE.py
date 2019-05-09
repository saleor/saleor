"""Auto-generated file, do not edit by hand. NE metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_NE = PhoneMetadata(id='NE', country_code=227, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[0289]\\d{7}', possible_length=(8,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='2(?:0(?:20|3[1-7]|4[13-5]|5[14]|6[14578]|7[1-578])|1(?:4[145]|5[14]|6[14-68]|7[169]|88))\\d{4}', example_number='20201234', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:8[04589]|9\\d)\\d{6}', example_number='93123456', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='08\\d{6}', example_number='08123456', possible_length=(8,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='09\\d{6}', example_number='09123456', possible_length=(8,)),
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['08']),
        NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[089]|2[01]'])])
