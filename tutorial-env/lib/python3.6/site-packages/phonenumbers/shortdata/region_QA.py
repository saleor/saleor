"""Auto-generated file, do not edit by hand. QA metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_QA = PhoneMetadata(id='QA', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[129]\\d{2,4}', possible_length=(3, 4, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='999', example_number='999', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='999', example_number='999', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='999|(?:1|20|9[27]\\d)\\d\\d', example_number='100', possible_length=(3, 4, 5)),
    short_data=True)
