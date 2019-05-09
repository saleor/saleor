"""Auto-generated file, do not edit by hand. PL metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_PL = PhoneMetadata(id='PL', country_code=48, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[1-57-9]\\d{6}(?:\\d{2})?|6\\d{5,8}', possible_length=(6, 7, 8, 9)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:1[2-8]|2[2-69]|3[2-4]|4[1-468]|5[24-689]|6[1-3578]|7[14-7]|8[1-79]|9[145])(?:[02-9]\\d{6}|1(?:[0-8]\\d{5}|9\\d{3}(?:\\d{2})?))', example_number='123456789', possible_length=(7, 9)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:45|5[0137]|6[069]|7[2389]|88)\\d{7}', example_number='512345678', possible_length=(9,)),
    toll_free=PhoneNumberDesc(national_number_pattern='800\\d{6}', example_number='800123456', possible_length=(9,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='70[01346-8]\\d{6}', example_number='701234567', possible_length=(9,)),
    shared_cost=PhoneNumberDesc(national_number_pattern='801\\d{6}', example_number='801234567', possible_length=(9,)),
    voip=PhoneNumberDesc(national_number_pattern='39\\d{7}', example_number='391234567', possible_length=(9,)),
    pager=PhoneNumberDesc(national_number_pattern='64\\d{4,7}', example_number='641234567', possible_length=(6, 7, 8, 9)),
    uan=PhoneNumberDesc(national_number_pattern='804\\d{6}', example_number='804123456', possible_length=(9,)),
    number_format=[NumberFormat(pattern='(\\d{5})', format='\\1', leading_digits_pattern=['19']),
        NumberFormat(pattern='(\\d{3})(\\d{3})', format='\\1 \\2', leading_digits_pattern=['11|64']),
        NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['(?:1[2-8]|2[2-69]|3[2-4]|4[1-468]|5[24-689]|6[1-3578]|7[14-7]|8[1-79]|9[145])1', '(?:1[2-8]|2[2-69]|3[2-4]|4[1-468]|5[24-689]|6[1-3578]|7[14-7]|8[1-79]|9[145])19']),
        NumberFormat(pattern='(\\d{3})(\\d{2})(\\d{2,3})', format='\\1 \\2 \\3', leading_digits_pattern=['64']),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['39|45|5[0137]|6[0469]|7[02389]|8[08]']),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['1[2-8]|[2-8]|9[145]'])],
    mobile_number_portable_region=True)
