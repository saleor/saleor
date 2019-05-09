"""Auto-generated file, do not edit by hand. WF metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_WF = PhoneMetadata(id='WF', country_code=681, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[45]0|68|72|8\\d)\\d{4}', possible_length=(6,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:50|68|72)\\d{4}', example_number='501234', possible_length=(6,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:50|68|72|8[23])\\d{4}', example_number='501234', possible_length=(6,)),
    voicemail=PhoneNumberDesc(national_number_pattern='[48]0\\d{4}', example_number='401234', possible_length=(6,)),
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3', leading_digits_pattern=['[4-8]'])])
