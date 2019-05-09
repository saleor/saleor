"""Auto-generated file, do not edit by hand. LB metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_LB = PhoneMetadata(id='LB', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[19]\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:12|40|75)|999', example_number='112', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:12|40|75)|999', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:12|40|75)|999', example_number='112', possible_length=(3,)),
    short_data=True)
