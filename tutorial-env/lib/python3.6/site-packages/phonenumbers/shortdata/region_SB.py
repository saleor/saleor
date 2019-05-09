"""Auto-generated file, do not edit by hand. SB metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_SB = PhoneMetadata(id='SB', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[127-9]\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='999', example_number='999', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='999', example_number='999', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:[02]\\d|1[12]|[35][01]|[49][1-9]|6[2-9]|7[7-9]|8[0-8])|269|777|835|9(?:[01]1|22|33|55|77|88|99)', example_number='100', possible_length=(3,)),
    short_data=True)
