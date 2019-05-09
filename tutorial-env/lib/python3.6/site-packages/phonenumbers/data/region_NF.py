"""Auto-generated file, do not edit by hand. NF metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_NF = PhoneMetadata(id='NF', country_code=672, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[13]\\d{5}', possible_length=(6,), possible_length_local_only=(5,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:1(?:06|17|28|39)|3[0-2]\\d)\\d{3}', example_number='106609', possible_length=(6,), possible_length_local_only=(5,)),
    mobile=PhoneNumberDesc(national_number_pattern='3[58]\\d{4}', example_number='381234', possible_length=(6,), possible_length_local_only=(5,)),
    national_prefix_for_parsing='([0-258]\\d{4})$',
    national_prefix_transform_rule='3\\1',
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['1']),
        NumberFormat(pattern='(\\d)(\\d{5})', format='\\1 \\2', leading_digits_pattern=['3'])])
