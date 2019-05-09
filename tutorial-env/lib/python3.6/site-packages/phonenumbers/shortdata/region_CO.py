"""Auto-generated file, do not edit by hand. CO metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_CO = PhoneMetadata(id='CO', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[148]\\d\\d(?:\\d{2})?', possible_length=(3, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:1[29]|23|32|56)', example_number='112', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:1[29]|23|32|56)', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:06|1[2569]|2[357]|3[27]|4[467]|5[36]|6[45]|95)|40404|85432', example_number='106', possible_length=(3, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='(?:40|85)4\\d\\d', example_number='40400', possible_length=(5,)),
    sms_services=PhoneNumberDesc(national_number_pattern='(?:40|85)4\\d\\d', example_number='40400', possible_length=(5,)),
    short_data=True)
