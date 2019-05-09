"""Auto-generated file, do not edit by hand. PT metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_PT = PhoneMetadata(id='PT', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d\\d(?:\\d{3})?', possible_length=(3, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='11(?:[25]|6\\d{3})', example_number='112', possible_length=(3, 6)),
    emergency=PhoneNumberDesc(national_number_pattern='11[25]', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='11(?:[2578]|6(?:000|111))', example_number='112', possible_length=(3, 6)),
    short_data=True)
