"""Auto-generated file, do not edit by hand. CM metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_CM = PhoneMetadata(id='CM', country_code=237, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[26]\\d\\d|88)\\d{6}', possible_length=(8, 9)),
    fixed_line=PhoneNumberDesc(national_number_pattern='2(?:22|33|4[23])\\d{6}', example_number='222123456', possible_length=(9,)),
    mobile=PhoneNumberDesc(national_number_pattern='6[5-9]\\d{7}', example_number='671234567', possible_length=(9,)),
    toll_free=PhoneNumberDesc(national_number_pattern='88\\d{6}', example_number='88012345', possible_length=(8,)),
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['88']),
        NumberFormat(pattern='(\\d)(\\d{2})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4 \\5', leading_digits_pattern=['[26]'])])
