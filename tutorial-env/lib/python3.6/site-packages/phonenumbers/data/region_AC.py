"""Auto-generated file, do not edit by hand. AC metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_AC = PhoneMetadata(id='AC', country_code=247, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[01589]\\d|[46])\\d{4}', possible_length=(5, 6)),
    fixed_line=PhoneNumberDesc(national_number_pattern='6[2-467]\\d{3}', example_number='62889', possible_length=(5,)),
    mobile=PhoneNumberDesc(national_number_pattern='4\\d{4}', example_number='40123', possible_length=(5,)),
    uan=PhoneNumberDesc(national_number_pattern='(?:0[1-9]|[1589]\\d)\\d{4}', example_number='542011', possible_length=(6,)))
