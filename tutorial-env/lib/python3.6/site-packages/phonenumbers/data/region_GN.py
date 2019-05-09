"""Auto-generated file, do not edit by hand. GN metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_GN = PhoneMetadata(id='GN', country_code=224, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:30|6\\d\\d|722)\\d{6}', possible_length=(8, 9)),
    fixed_line=PhoneNumberDesc(national_number_pattern='30(?:24|3[12]|4[1-35-7]|5[13]|6[189]|[78]1|9[1478])\\d{4}', example_number='30241234', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='6[02356]\\d{7}', example_number='601123456', possible_length=(9,)),
    voip=PhoneNumberDesc(national_number_pattern='722\\d{6}', example_number='722123456', possible_length=(9,)),
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['3']),
        NumberFormat(pattern='(\\d{3})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[67]'])])
