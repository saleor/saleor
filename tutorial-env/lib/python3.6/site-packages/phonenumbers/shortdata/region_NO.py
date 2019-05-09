"""Auto-generated file, do not edit by hand. NO metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_NO = PhoneMetadata(id='NO', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d\\d(?:\\d(?:\\d{2})?)?', possible_length=(3, 4, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='11(?:[023]|6\\d{3})', example_number='110', possible_length=(3, 6)),
    emergency=PhoneNumberDesc(national_number_pattern='11[023]', example_number='110', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:1(?:[0239]|61(?:1[17]|23))|2[048]|4(?:12|[59])|7[57]|90)', example_number='110', possible_length=(3, 4, 6)),
    short_data=True)
