"""Auto-generated file, do not edit by hand. TN metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_TN = PhoneMetadata(id='TN', country_code=216, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[2-57-9]\\d{7}', possible_length=(8,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='81200\\d{3}|(?:3[0-2]|7\\d)\\d{6}', example_number='30010123', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='3(?:001|[12]40)\\d{4}|(?:(?:[259]\\d|4[0-6])\\d|3(?:1[1-35]|6[0-4]|91))\\d{5}', example_number='20123456', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='8010\\d{4}', example_number='80101234', possible_length=(8,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='88\\d{6}', example_number='88123456', possible_length=(8,)),
    shared_cost=PhoneNumberDesc(national_number_pattern='8[12]10\\d{4}', example_number='81101234', possible_length=(8,)),
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['[2-57-9]'])])
