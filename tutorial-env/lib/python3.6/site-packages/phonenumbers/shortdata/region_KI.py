"""Auto-generated file, do not edit by hand. KI metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_KI = PhoneMetadata(id='KI', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[17]\\d{2,3}', possible_length=(3, 4)),
    toll_free=PhoneNumberDesc(national_number_pattern='19[2-5]', example_number='192', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='19[2-5]', example_number='192', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:05[0-259]|88|9[2-5])|777|10[0-8]', example_number='100', possible_length=(3, 4)),
    standard_rate=PhoneNumberDesc(national_number_pattern='103', example_number='103', possible_length=(3,)),
    short_data=True)
