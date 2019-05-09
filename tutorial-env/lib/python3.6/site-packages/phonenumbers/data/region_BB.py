"""Auto-generated file, do not edit by hand. BB metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_BB = PhoneMetadata(id='BB', country_code=1, international_prefix='011',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:246|[58]\\d\\d|900)\\d{7}', possible_length=(10,), possible_length_local_only=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='246(?:2(?:2[78]|7[0-4])|4(?:1[024-6]|2\\d|3[2-9])|5(?:20|[34]\\d|54|7[1-3])|6(?:2\\d|38)|7[35]7|9(?:1[89]|63))\\d{4}', example_number='2464123456', possible_length=(10,), possible_length_local_only=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='246(?:2(?:[356]\\d|4[0-57-9]|8[0-79])|45\\d|69[5-7]|8(?:[2-5]\\d|83))\\d{4}', example_number='2462501234', possible_length=(10,), possible_length_local_only=(7,)),
    toll_free=PhoneNumberDesc(national_number_pattern='8(?:00|33|44|55|66|77|88)[2-9]\\d{6}', example_number='8002123456', possible_length=(10,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='(?:246976|900[2-9]\\d\\d)\\d{4}', example_number='9002123456', possible_length=(10,), possible_length_local_only=(7,)),
    personal_number=PhoneNumberDesc(national_number_pattern='5(?:00|2[12]|33|44|66|77|88)[2-9]\\d{6}', example_number='5002345678', possible_length=(10,)),
    voip=PhoneNumberDesc(national_number_pattern='24631\\d{5}', example_number='2463101234', possible_length=(10,), possible_length_local_only=(7,)),
    uan=PhoneNumberDesc(national_number_pattern='246(?:292|367|4(?:1[7-9]|3[01]|44|67)|7(?:36|53))\\d{4}', example_number='2464301234', possible_length=(10,), possible_length_local_only=(7,)),
    national_prefix='1',
    national_prefix_for_parsing='1|([2-9]\\d{6})$',
    national_prefix_transform_rule='246\\1',
    leading_digits='246')
