"""Auto-generated file, do not edit by hand. MZ metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_MZ = PhoneMetadata(id='MZ', country_code=258, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:2|8\\d)\\d{7}', possible_length=(8, 9)),
    fixed_line=PhoneNumberDesc(national_number_pattern='2(?:[1346]\\d|5[0-2]|[78][12]|93)\\d{5}', example_number='21123456', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='8[2-7]\\d{7}', example_number='821234567', possible_length=(9,)),
    toll_free=PhoneNumberDesc(national_number_pattern='800\\d{6}', example_number='800123456', possible_length=(9,)),
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{3,4})', format='\\1 \\2 \\3', leading_digits_pattern=['2|8[2-7]']),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['8'])])
