"""Auto-generated file, do not edit by hand. ET metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_ET = PhoneMetadata(id='ET', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='9\\d\\d?', possible_length=(2, 3)),
    toll_free=PhoneNumberDesc(national_number_pattern='9(?:11?|[23]|9[17])', example_number='91', possible_length=(2, 3)),
    emergency=PhoneNumberDesc(national_number_pattern='9(?:11?|[23]|9[17])', example_number='91', possible_length=(2, 3)),
    short_code=PhoneNumberDesc(national_number_pattern='9(?:11?|[23]|9[17])', example_number='91', possible_length=(2, 3)),
    short_data=True)
