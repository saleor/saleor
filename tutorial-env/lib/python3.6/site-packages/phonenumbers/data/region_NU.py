"""Auto-generated file, do not edit by hand. NU metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_NU = PhoneMetadata(id='NU', country_code=683, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[47]|888\\d)\\d{3}', possible_length=(4, 7)),
    fixed_line=PhoneNumberDesc(national_number_pattern='[47]\\d{3}', example_number='7012', possible_length=(4,)),
    mobile=PhoneNumberDesc(national_number_pattern='888[4-9]\\d{3}', example_number='8884012', possible_length=(7,)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['8'])])
