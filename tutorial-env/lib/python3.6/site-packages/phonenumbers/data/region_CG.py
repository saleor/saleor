"""Auto-generated file, do not edit by hand. CG metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_CG = PhoneMetadata(id='CG', country_code=242, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='222\\d{6}|(?:0\\d|80)\\d{7}', possible_length=(9,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='222[1-589]\\d{5}', example_number='222123456', possible_length=(9,)),
    mobile=PhoneNumberDesc(national_number_pattern='0[14-6]\\d{7}', example_number='061234567', possible_length=(9,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='80(?:0\\d\\d|11[0-4])\\d{4}', example_number='800123456', possible_length=(9,)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['801']),
        NumberFormat(pattern='(\\d)(\\d{4})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['8']),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['[02]'])])
