"""Auto-generated file, do not edit by hand. AT metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_AT = PhoneMetadata(id='AT', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d\\d(?:\\d{3})?', possible_length=(3, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='116\\d{3}|1(?:[12]2|33|44)', example_number='112', possible_length=(3, 6)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:[12]2|33|44)', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='116(?:00[06]|1(?:17|23))|1(?:[12]2|33|44)', example_number='112', possible_length=(3, 6)),
    short_data=True)
