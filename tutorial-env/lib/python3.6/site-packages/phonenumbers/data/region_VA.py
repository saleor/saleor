"""Auto-generated file, do not edit by hand. VA metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_VA = PhoneMetadata(id='VA', country_code=39, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='0\\d{6,10}|55\\d{8}|[08]\\d{5}|(?:3[0-8]|8)\\d{7,9}|(?:1\\d|39)\\d{7,8}', possible_length=(6, 7, 8, 9, 10, 11)),
    fixed_line=PhoneNumberDesc(national_number_pattern='06698\\d{1,6}', example_number='0669812345', possible_length=(6, 7, 8, 9, 10, 11)),
    mobile=PhoneNumberDesc(national_number_pattern='33\\d{9}|3[1-9]\\d{8}|3[2-9]\\d{7}', example_number='3123456789', possible_length=(9, 10, 11)),
    toll_free=PhoneNumberDesc(national_number_pattern='80(?:0\\d{3}|3)\\d{3}', example_number='800123456', possible_length=(6, 9)),
    premium_rate=PhoneNumberDesc(national_number_pattern='(?:0878\\d\\d|89(?:2|4[5-9]\\d))\\d{3}|89[45][0-4]\\d\\d|(?:1(?:44|6[346])|89(?:5[5-9]|9))\\d{6}', example_number='899123456', possible_length=(6, 8, 9, 10)),
    shared_cost=PhoneNumberDesc(national_number_pattern='84(?:[08]\\d{3}|[17])\\d{3}', example_number='848123456', possible_length=(6, 9)),
    personal_number=PhoneNumberDesc(national_number_pattern='1(?:78\\d|99)\\d{6}', example_number='1781234567', possible_length=(9, 10)),
    voip=PhoneNumberDesc(national_number_pattern='55\\d{8}', example_number='5512345678', possible_length=(10,)),
    leading_digits='06698',
    mobile_number_portable_region=True)
