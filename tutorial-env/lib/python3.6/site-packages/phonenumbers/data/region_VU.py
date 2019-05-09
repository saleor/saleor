"""Auto-generated file, do not edit by hand. VU metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_VU = PhoneMetadata(id='VU', country_code=678, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[23]\\d|[48]8)\\d{3}|(?:[57]\\d|90)\\d{5}', possible_length=(5, 7)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:38[0-8]|48[4-9])\\d\\d|(?:2[02-9]|3[4-7]|88)\\d{3}', example_number='22123', possible_length=(5,)),
    mobile=PhoneNumberDesc(national_number_pattern='57[2-5]\\d{4}|(?:5[0-689]|7[013-7])\\d{5}', example_number='5912345', possible_length=(7,)),
    voip=PhoneNumberDesc(national_number_pattern='90[1-9]\\d{4}', example_number='9010123', possible_length=(7,)),
    uan=PhoneNumberDesc(national_number_pattern='(?:3[03]|900\\d)\\d{3}', example_number='30123', possible_length=(5, 7)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[579]'])])
