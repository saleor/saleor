"""Auto-generated file, do not edit by hand. FJ metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_FJ = PhoneMetadata(id='FJ', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[0-579]\\d(?:\\d(?:\\d{2})?)?', possible_length=(2, 3, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='91[17]', example_number='911', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='91[17]', example_number='911', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='0(?:1[34]|8[1-4])|1(?:0[1-3]|[25]9)|2[289]|30|40404|91[137]|[45]4|75', example_number='22', possible_length=(2, 3, 5)),
    sms_services=PhoneNumberDesc(national_number_pattern='404\\d\\d', example_number='40400', possible_length=(5,)),
    short_data=True)
