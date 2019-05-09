"""Auto-generated file, do not edit by hand. NZ metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_NZ = PhoneMetadata(id='NZ', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='\\d{3,4}', possible_length=(3, 4)),
    toll_free=PhoneNumberDesc(national_number_pattern='111', example_number='111', possible_length=(3,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='018', example_number='018', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='111', example_number='111', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='018|1(?:(?:1|37)1|(?:23|94)4|7[03]7)|[2-57-9]\\d{2,3}|6(?:161|26[0-3]|742)', example_number='018', possible_length=(3, 4)),
    sms_services=PhoneNumberDesc(national_number_pattern='018|(?:1(?:23|37|7[03]|94)|6(?:[12]6|74))\\d|[2-57-9]\\d{2,3}', example_number='018', possible_length=(3, 4)),
    short_data=True)
