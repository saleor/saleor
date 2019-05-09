"""Auto-generated file, do not edit by hand. TR metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_TR = PhoneMetadata(id='TR', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[1-9]\\d{2,4}', possible_length=(3, 4, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:1[02]|22|3[126]|4[04]|5[15-9]|6[18]|77|83)', example_number='110', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:1[02]|55)', example_number='110', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:1(?:[0239]|811)|2[126]|3(?:[12]|37?|[58]6|65?)|4(?:[014]|71)|5(?:07|[135689]|78?)|6(?:[02]6|[138]|99?)|7[0-79]|8(?:[0-578]|63?|95?))|2(?:077|268|4(?:17|23)|5(?:7[26]|82)|6[14]4|8\\d\\d|9(?:30|89))|3(?:0(?:05|72)|353|4(?:06|30|64)|502|674|747|851|9(?:1[29]|60))|4(?:0(?:25|3[12]|[47]2)|3(?:3[13]|[89]1)|439|5(?:43|55)|717|832)|5(?:145|290|[4-6]\\d\\d|772|833|9(?:[06]1|92))|6(?:236|6(?:12|39|8[59])|769)|7890|8(?:688|7(?:28|65)|85[06])|9(?:159|290)', example_number='110', possible_length=(3, 4, 5)),
    standard_rate=PhoneNumberDesc(national_number_pattern='(?:285|542)0', example_number='2850', possible_length=(4,)),
    sms_services=PhoneNumberDesc(national_number_pattern='1(?:3(?:37|65)|44|578|699|8(?:3|63|95))|(?:1(?:3[58]|47|50|6[02])|2(?:07|26|4[12]|5[78]|6[14]|8\\d|9[38])|3(?:0[07]|[38]5|4[036]|50|67|74|9[16])|4(?:0[2-47]|3[389]|[48]3|5[45]|71)|5(?:14|29|[4-6]\\d|77|83|9[069])|6(?:23|6[138]|76)|789|8(?:68|7[26]|85)|9(?:15|29))\\d', example_number='144', possible_length=(3, 4)),
    short_data=True)
