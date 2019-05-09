"""Auto-generated file, do not edit by hand. GP metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_GP = PhoneMetadata(id='GP', country_code=590, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:590|69\\d)\\d{6}', possible_length=(9,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='590(?:0[1-68]|1[0-2]|2[0-68]|3[1289]|4[0-24-9]|5[3-579]|6[0189]|7[08]|8[0-689]|9\\d)\\d{4}', example_number='590201234', possible_length=(9,)),
    mobile=PhoneNumberDesc(national_number_pattern='69(?:0\\d\\d|1(?:2[29]|3[0-5]))\\d{4}', example_number='690001234', possible_length=(9,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[56]'], national_prefix_formatting_rule='0\\1')],
    main_country_for_code=True,
    mobile_number_portable_region=True)
