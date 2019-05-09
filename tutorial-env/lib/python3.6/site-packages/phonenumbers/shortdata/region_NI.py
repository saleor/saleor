"""Auto-generated file, do not edit by hand. NI metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_NI = PhoneMetadata(id='NI', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[12467]\\d{2,3}', possible_length=(3, 4)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:1[58]|2[08])|737\\d', example_number='115', possible_length=(3, 4)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:1[58]|2[08])', example_number='115', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:1[58]|200)|4878|7(?:010|373)|12[0158]|(?:19|[267]1)00', example_number='115', possible_length=(3, 4)),
    short_data=True)
