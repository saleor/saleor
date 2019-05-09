"""Auto-generated file, do not edit by hand. BS metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_BS = PhoneMetadata(id='BS', country_code=1, international_prefix='011',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:242|[58]\\d\\d|900)\\d{7}', possible_length=(10,), possible_length_local_only=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='242(?:3(?:02|[236][1-9]|4[0-24-9]|5[0-68]|7[347]|8[0-4]|9[2-467])|461|502|6(?:0[1-4]|12|2[013]|[45]0|7[67]|8[78]|9[89])|7(?:02|88))\\d{4}', example_number='2423456789', possible_length=(10,), possible_length_local_only=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='242(?:3(?:5[79]|7[56]|95)|4(?:[23][1-9]|4[1-35-9]|5[1-8]|6[2-8]|7\\d|81)|5(?:2[45]|3[35]|44|5[1-46-9]|65|77)|6[34]6|7(?:27|38)|8(?:0[1-9]|1[02-9]|2\\d|[89]9))\\d{4}', example_number='2423591234', possible_length=(10,), possible_length_local_only=(7,)),
    toll_free=PhoneNumberDesc(national_number_pattern='242300\\d{4}|8(?:00|33|44|55|66|77|88)[2-9]\\d{6}', example_number='8002123456', possible_length=(10,), possible_length_local_only=(7,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='900[2-9]\\d{6}', example_number='9002123456', possible_length=(10,)),
    personal_number=PhoneNumberDesc(national_number_pattern='5(?:00|2[12]|33|44|66|77|88)[2-9]\\d{6}', example_number='5002345678', possible_length=(10,)),
    uan=PhoneNumberDesc(national_number_pattern='242225[0-46-9]\\d{3}', example_number='2422250123', possible_length=(10,)),
    national_prefix='1',
    national_prefix_for_parsing='1|([3-8]\\d{6})$',
    national_prefix_transform_rule='242\\1',
    leading_digits='242',
    mobile_number_portable_region=True)
