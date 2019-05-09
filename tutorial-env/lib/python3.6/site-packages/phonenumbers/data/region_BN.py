"""Auto-generated file, do not edit by hand. BN metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_BN = PhoneMetadata(id='BN', country_code=673, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[2-578]\\d{6}', possible_length=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='22[0-7]\\d{4}|(?:2[013-9]|[3-5]\\d)\\d{5}', example_number='2345678', possible_length=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:22[89]|[78]\\d\\d)\\d{4}', example_number='7123456', possible_length=(7,)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[2-578]'])])
