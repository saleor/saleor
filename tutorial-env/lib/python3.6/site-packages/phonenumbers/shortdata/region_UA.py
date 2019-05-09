"""Auto-generated file, do not edit by hand. UA metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_UA = PhoneMetadata(id='UA', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[189]\\d{2,5}', possible_length=(3, 4, 5, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:0[1-3]|1(?:2|6\\d{3}))', example_number='101', possible_length=(3, 6)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:0[1-3]|12)', example_number='101', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:0[1-49]|1(?:2|6(?:000|1(?:11|23))|8\\d\\d?)|(?:[278]|5\\d)\\d)|[89]00\\d\\d?|151|1(?:06|4\\d|6)\\d\\d', example_number='101', possible_length=(3, 4, 5, 6)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='(?:118|[89]00)\\d\\d?', example_number='1180', possible_length=(4, 5)),
    short_data=True)
