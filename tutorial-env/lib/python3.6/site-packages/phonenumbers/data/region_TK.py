"""Auto-generated file, do not edit by hand. TK metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_TK = PhoneMetadata(id='TK', country_code=690, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[2-47]\\d{3,6}', possible_length=(4, 5, 6, 7)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:2[2-4]|[34]\\d)\\d{2,5}', example_number='3101', possible_length=(4, 5, 6, 7)),
    mobile=PhoneNumberDesc(national_number_pattern='7[2-4]\\d{2,5}', example_number='7290', possible_length=(4, 5, 6, 7)))
