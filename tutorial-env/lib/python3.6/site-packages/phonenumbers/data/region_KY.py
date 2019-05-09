"""Auto-generated file, do not edit by hand. KY metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_KY = PhoneMetadata(id='KY', country_code=1, international_prefix='011',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:345|[58]\\d\\d|900)\\d{7}', possible_length=(10,), possible_length_local_only=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='345(?:2(?:22|44)|444|6(?:23|38|40)|7(?:4[35-79]|6[6-9]|77)|8(?:00|1[45]|25|[48]8)|9(?:14|4[035-9]))\\d{4}', example_number='3452221234', possible_length=(10,), possible_length_local_only=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='345(?:32[1-9]|5(?:1[67]|2[5-79]|4[6-9]|50|76)|649|9(?:1[67]|2[2-9]|3[689]))\\d{4}', example_number='3453231234', possible_length=(10,), possible_length_local_only=(7,)),
    toll_free=PhoneNumberDesc(national_number_pattern='8(?:00|33|44|55|66|77|88)[2-9]\\d{6}', example_number='8002345678', possible_length=(10,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='(?:345976|900[2-9]\\d\\d)\\d{4}', example_number='9002345678', possible_length=(10,)),
    personal_number=PhoneNumberDesc(national_number_pattern='5(?:00|2[12]|33|44|66|77|88)[2-9]\\d{6}', example_number='5002345678', possible_length=(10,)),
    pager=PhoneNumberDesc(national_number_pattern='345849\\d{4}', example_number='3458491234', possible_length=(10,)),
    national_prefix='1',
    national_prefix_for_parsing='1|([2-9]\\d{6})$',
    national_prefix_transform_rule='345\\1',
    leading_digits='345',
    mobile_number_portable_region=True)
