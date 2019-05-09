"""Auto-generated file, do not edit by hand. LS metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_LS = PhoneMetadata(id='LS', country_code=266, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[256]\\d\\d|800)\\d{5}', possible_length=(8,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='2\\d{7}', example_number='22123456', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='[56]\\d{7}', example_number='50123456', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='800[256]\\d{4}', example_number='80021234', possible_length=(8,)),
    number_format=[NumberFormat(pattern='(\\d{4})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[2568]'])])
