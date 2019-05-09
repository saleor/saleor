"""Auto-generated file, do not edit by hand. BJ metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_BJ = PhoneMetadata(id='BJ', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[17]\\d{2,3}', possible_length=(3, 4)),
    toll_free=PhoneNumberDesc(national_number_pattern='11[78]|7[3-5]\\d\\d', example_number='117', possible_length=(3, 4)),
    emergency=PhoneNumberDesc(national_number_pattern='11[78]', example_number='117', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:1[78]|2[02-5]|60)|7[0-5]\\d\\d', example_number='117', possible_length=(3, 4)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='12[02-5]', example_number='120', possible_length=(3,)),
    short_data=True)
