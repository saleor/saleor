"""Auto-generated file, do not edit by hand. CV metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_CV = PhoneMetadata(id='CV', country_code=238, international_prefix='0',
    general_desc=PhoneNumberDesc(national_number_pattern='[2-59]\\d{6}', possible_length=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='2(?:2[1-7]|3[0-8]|4[12]|5[1256]|6\\d|7[1-3]|8[1-5])\\d{4}', example_number='2211234', possible_length=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:[34][36]|5[1-389]|9\\d)\\d{5}', example_number='9911234', possible_length=(7,)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{2})(\\d{2})', format='\\1 \\2 \\3', leading_digits_pattern=['[2-59]'])])
