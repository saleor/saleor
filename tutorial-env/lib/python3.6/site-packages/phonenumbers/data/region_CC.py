"""Auto-generated file, do not edit by hand. CC metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_CC = PhoneMetadata(id='CC', country_code=61, international_prefix='001[14-689]|14(?:1[14]|34|4[17]|[56]6|7[47]|88)0011',
    general_desc=PhoneNumberDesc(national_number_pattern='1(?:[0-79]\\d|8[0-24-9])\\d{7}|(?:[148]\\d\\d|550)\\d{6}|1\\d{5,7}', possible_length=(6, 7, 8, 9, 10), possible_length_local_only=(8,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='8(?:51(?:0(?:02|31|60)|118)|91(?:0(?:1[0-2]|29)|1(?:[28]2|50|79)|2(?:10|64)|3(?:[06]8|22)|4[29]8|62\\d|70[23]|959))\\d{3}', example_number='891621234', possible_length=(9,), possible_length_local_only=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='4(?:[0-3]\\d|4[047-9]|5[0-25-9]|6[6-9]|7[02-9]|8[0-2457-9]|9[017-9])\\d{6}', example_number='412345678', possible_length=(9,)),
    toll_free=PhoneNumberDesc(national_number_pattern='180(?:0\\d{3}|2)\\d{3}', example_number='1800123456', possible_length=(7, 10)),
    premium_rate=PhoneNumberDesc(national_number_pattern='190[0-26]\\d{6}', example_number='1900123456', possible_length=(10,)),
    shared_cost=PhoneNumberDesc(national_number_pattern='13(?:00\\d{3}|45[0-4])\\d{3}|13\\d{4}', example_number='1300123456', possible_length=(6, 8, 10)),
    voip=PhoneNumberDesc(national_number_pattern='(?:14(?:5(?:1[0458]|[23][458])|71\\d)|550\\d\\d)\\d{4}', example_number='550123456', possible_length=(9,)),
    preferred_international_prefix='0011',
    national_prefix='0',
    national_prefix_for_parsing='0|([59]\\d{7})$',
    national_prefix_transform_rule='8\\1')
