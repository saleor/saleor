"""Auto-generated file, do not edit by hand. CW metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_CW = PhoneMetadata(id='CW', country_code=599, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[34]1|60|(?:7|9\\d)\\d)\\d{5}', possible_length=(7, 8)),
    fixed_line=PhoneNumberDesc(national_number_pattern='9(?:4(?:3[0-5]|4[14]|6\\d)|50\\d|7(?:2[014]|3[02-9]|4[4-9]|6[357]|77|8[7-9])|8(?:3[39]|[46]\\d|7[01]|8[57-9]))\\d{4}', example_number='94351234', possible_length=(7, 8)),
    mobile=PhoneNumberDesc(national_number_pattern='953[01]\\d{4}|9(?:5[12467]|6[5-9])\\d{5}', example_number='95181234', possible_length=(7, 8)),
    shared_cost=PhoneNumberDesc(national_number_pattern='60[0-2]\\d{4}', example_number='6001234', possible_length=(7,)),
    pager=PhoneNumberDesc(national_number_pattern='955\\d{5}', example_number='95581234', possible_length=(8,)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[3467]']),
        NumberFormat(pattern='(\\d)(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['9[4-8]'])],
    main_country_for_code=True,
    leading_digits='[69]')
