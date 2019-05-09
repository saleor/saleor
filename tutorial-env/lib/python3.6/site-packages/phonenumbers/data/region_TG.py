"""Auto-generated file, do not edit by hand. TG metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_TG = PhoneMetadata(id='TG', country_code=228, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[279]\\d{7}', possible_length=(8,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='2(?:2[2-7]|3[23]|4[45]|55|6[67]|77)\\d{5}', example_number='22212345', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:7[09]|9[0-36-9])\\d{6}', example_number='90112345', possible_length=(8,)),
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[279]'])])
