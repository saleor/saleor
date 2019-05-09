"""Auto-generated file, do not edit by hand. LV metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_LV = PhoneMetadata(id='LV', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[018]\\d{1,5}', possible_length=(2, 3, 4, 5, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='0[1-3]|11(?:[023]|6\\d{3})', example_number='01', possible_length=(2, 3, 6)),
    premium_rate=PhoneNumberDesc(national_number_pattern='1180|821\\d\\d', example_number='1180', possible_length=(4, 5)),
    emergency=PhoneNumberDesc(national_number_pattern='0[1-3]|11[023]', example_number='01', possible_length=(2, 3)),
    short_code=PhoneNumberDesc(national_number_pattern='0[1-4]|1(?:1(?:[02-4]|6(?:000|111)|8[0189])|(?:5|65)5|77)|821[57]4', example_number='01', possible_length=(2, 3, 4, 5, 6)),
    standard_rate=PhoneNumberDesc(national_number_pattern='1181', example_number='1181', possible_length=(4,)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='165\\d', example_number='1650', possible_length=(4,)),
    short_data=True)
