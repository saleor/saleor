"""Auto-generated file, do not edit by hand. CM metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_CM = PhoneMetadata(id='CM', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[18]\\d{1,3}', possible_length=(2, 3, 4)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:1[37]|[37])', example_number='13', possible_length=(2, 3)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:1[37]|[37])', example_number='13', possible_length=(2, 3)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:1[37]|[37])|8711', example_number='13', possible_length=(2, 3, 4)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='871\\d', example_number='8710', possible_length=(4,)),
    sms_services=PhoneNumberDesc(national_number_pattern='871\\d', example_number='8710', possible_length=(4,)),
    short_data=True)
