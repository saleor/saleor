"""Auto-generated file, do not edit by hand. GW metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_GW = PhoneMetadata(id='GW', country_code=245, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[49]\\d{8}|4\\d{6}', possible_length=(7, 9)),
    fixed_line=PhoneNumberDesc(national_number_pattern='443\\d{6}', example_number='443201234', possible_length=(9,)),
    mobile=PhoneNumberDesc(national_number_pattern='9(?:5\\d|6[569]|77)\\d{6}', example_number='955012345', possible_length=(9,)),
    voip=PhoneNumberDesc(national_number_pattern='40\\d{5}', example_number='4012345', possible_length=(7,)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['40']),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['[49]'])])
