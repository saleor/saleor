"""Auto-generated file, do not edit by hand. GF metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_GF = PhoneMetadata(id='GF', country_code=594, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[56]94\\d{6}', possible_length=(9,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='594(?:[023]\\d|1[01]|4[03-9]|5[6-9]|6[0-3]|80|9[014])\\d{4}', example_number='594101234', possible_length=(9,)),
    mobile=PhoneNumberDesc(national_number_pattern='694(?:[0-249]\\d|3[0-48])\\d{4}', example_number='694201234', possible_length=(9,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[56]'], national_prefix_formatting_rule='0\\1')],
    mobile_number_portable_region=True)
