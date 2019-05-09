"""Auto-generated file, do not edit by hand. OM metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_OM = PhoneMetadata(id='OM', country_code=968, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[279]\\d{3}|500)\\d{4}|8007\\d{4,5}', possible_length=(7, 8, 9)),
    fixed_line=PhoneNumberDesc(national_number_pattern='2[2-6]\\d{6}', example_number='23123456', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='90[1-9]\\d{5}|(?:7[129]|9[1-9])\\d{6}', example_number='92123456', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='500\\d{4}|8007\\d{4,5}', example_number='80071234', possible_length=(7, 8, 9)),
    premium_rate=PhoneNumberDesc(national_number_pattern='900\\d{5}', example_number='90012345', possible_length=(8,)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{4,6})', format='\\1 \\2', leading_digits_pattern=['[58]']),
        NumberFormat(pattern='(\\d{2})(\\d{6})', format='\\1 \\2', leading_digits_pattern=['2']),
        NumberFormat(pattern='(\\d{4})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[79]'])],
    mobile_number_portable_region=True)
