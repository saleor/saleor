"""Auto-generated file, do not edit by hand. MC metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_MC = PhoneMetadata(id='MC', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d\\d?', possible_length=(2, 3)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:12|[578])', example_number='15', possible_length=(2, 3)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:12|[578])', example_number='15', possible_length=(2, 3)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:12|41|[578])', example_number='15', possible_length=(2, 3)),
    short_data=True)
