"""Auto-generated file, do not edit by hand. OM metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_OM = PhoneMetadata(id='OM', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='9\\d{3}', possible_length=(4,)),
    toll_free=PhoneNumberDesc(national_number_pattern='999\\d', example_number='9990', possible_length=(4,)),
    emergency=PhoneNumberDesc(national_number_pattern='9999', example_number='9999', possible_length=(4,)),
    short_code=PhoneNumberDesc(national_number_pattern='9999', example_number='9999', possible_length=(4,)),
    short_data=True)
