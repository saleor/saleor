"""Auto-generated file, do not edit by hand. FI metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_FI = PhoneMetadata(id='FI', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[17]\\d\\d(?:\\d{2,3})?', possible_length=(3, 5, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='11(?:2|6\\d{3})', example_number='112', possible_length=(3, 6)),
    emergency=PhoneNumberDesc(national_number_pattern='112', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='11(?:2|6111)|75[12]\\d\\d', example_number='112', possible_length=(3, 5, 6)),
    short_data=True)
