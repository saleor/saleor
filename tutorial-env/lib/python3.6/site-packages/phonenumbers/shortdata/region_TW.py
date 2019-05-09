"""Auto-generated file, do not edit by hand. TW metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_TW = PhoneMetadata(id='TW', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d{2,3}', possible_length=(3, 4)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:1[0289]|92\\d)', example_number='110', possible_length=(3, 4)),
    premium_rate=PhoneNumberDesc(national_number_pattern='10[56]', example_number='105', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='11[029]', example_number='110', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:0[4-6]|1[02389]|6[5-8]|9(?:1[0-29]|22|5[057]|68|8[05]|9[15689]))', example_number='104', possible_length=(3, 4)),
    standard_rate=PhoneNumberDesc(national_number_pattern='1(?:65|9(?:19|50|85|98))', example_number='165', possible_length=(3, 4)),
    short_data=True)
