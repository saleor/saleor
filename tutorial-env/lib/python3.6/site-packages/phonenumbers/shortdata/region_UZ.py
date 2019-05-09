"""Auto-generated file, do not edit by hand. UZ metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_UZ = PhoneMetadata(id='UZ', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[04]\\d(?:\\d(?:\\d{2})?)?', possible_length=(2, 3, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='0(?:0[1-3]|[1-3]|50)', example_number='01', possible_length=(2, 3)),
    emergency=PhoneNumberDesc(national_number_pattern='0(?:0[1-3]|[1-3]|50)', example_number='01', possible_length=(2, 3)),
    short_code=PhoneNumberDesc(national_number_pattern='0(?:0[1-3]|[1-3]|50)|45400', example_number='01', possible_length=(2, 3, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='454\\d\\d', example_number='45400', possible_length=(5,)),
    sms_services=PhoneNumberDesc(national_number_pattern='454\\d\\d', example_number='45400', possible_length=(5,)),
    short_data=True)
