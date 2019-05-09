"""Auto-generated file, do not edit by hand. BY metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_BY = PhoneMetadata(id='BY', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d\\d', possible_length=(3,)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:0[1-3]|12)', example_number='101', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:0[1-3]|12)', example_number='101', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:0[1-79]|1[246]|35|5[1-35]|6[89]|7[5-7]|8[58]|9[1-7])', example_number='101', possible_length=(3,)),
    short_data=True)
