"""Auto-generated file, do not edit by hand. AR metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_AR = PhoneMetadata(id='AR', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[01389]\\d{1,4}', possible_length=(2, 3, 4, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='000|1(?:0[0-35-7]|1[0245]|2[15]|9)|911', example_number='19', possible_length=(2, 3)),
    emergency=PhoneNumberDesc(national_number_pattern='10[017]|911', example_number='100', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='000|1(?:0[0-35-7]|1[02-5]|2[15]|9)|3372|89338|911', example_number='19', possible_length=(2, 3, 4, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='893\\d\\d', example_number='89300', possible_length=(5,)),
    sms_services=PhoneNumberDesc(national_number_pattern='(?:337|893\\d)\\d', example_number='3370', possible_length=(4, 5)),
    short_data=True)
