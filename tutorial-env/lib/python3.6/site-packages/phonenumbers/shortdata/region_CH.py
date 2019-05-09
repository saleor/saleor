"""Auto-generated file, do not edit by hand. CH metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_CH = PhoneMetadata(id='CH', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[1-9]\\d{2,5}', possible_length=(3, 4, 5, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:1(?:[278]|6\\d{3})|4[47])|5200', example_number='112', possible_length=(3, 4, 6)),
    premium_rate=PhoneNumberDesc(national_number_pattern='1(?:14|8[01589])\\d|543|83111', example_number='543', possible_length=(3, 4, 5)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:1[278]|44)', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:0[78]\\d\\d|1(?:[278]|45|6(?:000|111))|4(?:[03-57]|1[45])|6(?:00|[1-46])|8(?:02|1[189]|50|7|8[08]|99))|[2-9]\\d{2,4}', example_number='112', possible_length=(3, 4, 5, 6)),
    standard_rate=PhoneNumberDesc(national_number_pattern='1(?:4[035]|6[1-46])|1(?:41|60)\\d', example_number='140', possible_length=(3, 4)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='5(?:200|35)', example_number='535', possible_length=(3, 4)),
    sms_services=PhoneNumberDesc(national_number_pattern='[2-9]\\d{2,4}', example_number='200', possible_length=(3, 4, 5)),
    short_data=True)
