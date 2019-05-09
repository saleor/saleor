"""Auto-generated file, do not edit by hand. SA metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_SA = PhoneMetadata(id='SA', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[19]\\d{2,5}', possible_length=(3, 4, 5, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='11(?:2|6\\d{3})|9(?:11|37|9[7-9])', example_number='112', possible_length=(3, 6)),
    emergency=PhoneNumberDesc(national_number_pattern='112|9(?:11|9[79])', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:1(?:00|2|6111)|410|9(?:00|1[89]|9(?:099|22|91)))|9(?:0[24-79]|11|3[379]|40|66|8[5-9]|9[02-9])', example_number='112', possible_length=(3, 4, 5, 6)),
    standard_rate=PhoneNumberDesc(national_number_pattern='141\\d', example_number='1410', possible_length=(4,)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='1(?:10|41)\\d|90[24679]', example_number='902', possible_length=(3, 4)),
    short_data=True)
