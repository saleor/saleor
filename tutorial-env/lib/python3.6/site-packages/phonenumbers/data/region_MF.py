"""Auto-generated file, do not edit by hand. MF metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_MF = PhoneMetadata(id='MF', country_code=590, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:590|69\\d)\\d{6}', possible_length=(9,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='590(?:0[079]|[14]3|[27][79]|30|5[0-268]|87)\\d{4}', example_number='590271234', possible_length=(9,)),
    mobile=PhoneNumberDesc(national_number_pattern='69(?:0\\d\\d|1(?:2[29]|3[0-5]))\\d{4}', example_number='690001234', possible_length=(9,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    mobile_number_portable_region=True)
