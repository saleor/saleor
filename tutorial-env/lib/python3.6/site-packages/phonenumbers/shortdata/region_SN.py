"""Auto-generated file, do not edit by hand. SN metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_SN = PhoneMetadata(id='SN', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[12]\\d{1,5}', possible_length=(2, 3, 4, 5, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:515|[78])|2(?:00|1)\\d{3}', example_number='17', possible_length=(2, 4, 5, 6)),
    premium_rate=PhoneNumberDesc(national_number_pattern='2(?:0[246]|[468])\\d{3}', example_number='24000', possible_length=(5, 6)),
    emergency=PhoneNumberDesc(national_number_pattern='1[78]', example_number='17', possible_length=(2,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:1[69]|(?:[246]\\d|51)\\d)|2(?:0[0-246]|[12468])\\d{3}|1[278]', example_number='12', possible_length=(2, 3, 4, 5, 6)),
    standard_rate=PhoneNumberDesc(national_number_pattern='2(?:01|2)\\d{3}', example_number='22000', possible_length=(5, 6)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='1[46]\\d\\d', example_number='1400', possible_length=(4,)),
    sms_services=PhoneNumberDesc(national_number_pattern='2[468]\\d{3}', example_number='24000', possible_length=(5,)),
    short_data=True)
