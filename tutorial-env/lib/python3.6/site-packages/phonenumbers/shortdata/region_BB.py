"""Auto-generated file, do not edit by hand. BB metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_BB = PhoneMetadata(id='BB', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[2-689]\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='[2359]11', example_number='211', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='[2359]11', example_number='211', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='[2-689]11', example_number='211', possible_length=(3,)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='[468]11', example_number='411', possible_length=(3,)),
    short_data=True)
