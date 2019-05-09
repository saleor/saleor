"""Auto-generated file, do not edit by hand. GT metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_GT = PhoneMetadata(id='GT', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[14]\\d{2,4}', possible_length=(3, 4, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:10|2[03])', example_number='110', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:10|2[03])', example_number='110', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='110|40404|1(?:2|[57]\\d)\\d', example_number='110', possible_length=(3, 4, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='404\\d\\d', example_number='40400', possible_length=(5,)),
    sms_services=PhoneNumberDesc(national_number_pattern='404\\d\\d', example_number='40400', possible_length=(5,)),
    short_data=True)
