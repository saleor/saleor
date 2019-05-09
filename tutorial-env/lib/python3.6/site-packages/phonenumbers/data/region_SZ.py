"""Auto-generated file, do not edit by hand. SZ metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_SZ = PhoneMetadata(id='SZ', country_code=268, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='0800\\d{4}|(?:[237]\\d|900)\\d{6}', possible_length=(8, 9)),
    fixed_line=PhoneNumberDesc(national_number_pattern='[23][2-5]\\d{6}', example_number='22171234', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='7[6-9]\\d{6}', example_number='76123456', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='0800\\d{4}', example_number='08001234', possible_length=(8,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='900\\d{6}', example_number='900012345', possible_length=(9,)),
    voip=PhoneNumberDesc(national_number_pattern='70\\d{6}', example_number='70012345', possible_length=(8,)),
    no_international_dialling=PhoneNumberDesc(national_number_pattern='0800\\d{4}', possible_length=(8,)),
    number_format=[NumberFormat(pattern='(\\d{4})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[0237]']),
        NumberFormat(pattern='(\\d{5})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['9'])])
