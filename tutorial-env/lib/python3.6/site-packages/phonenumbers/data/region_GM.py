"""Auto-generated file, do not edit by hand. GM metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_GM = PhoneMetadata(id='GM', country_code=220, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[2-9]\\d{6}', possible_length=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:4(?:[23]\\d\\d|4(?:1[024679]|[6-9]\\d))|5(?:54[0-7]|6[67]\\d|7(?:1[04]|2[035]|3[58]|48))|8\\d{3})\\d{3}', example_number='5661234', possible_length=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:[23679]\\d|5[01])\\d{5}', example_number='3012345', possible_length=(7,)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[2-9]'])])
