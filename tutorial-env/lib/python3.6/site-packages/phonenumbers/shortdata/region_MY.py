"""Auto-generated file, do not edit by hand. MY metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_MY = PhoneMetadata(id='MY', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[1369]\\d{2,4}', possible_length=(3, 4, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='112|999', example_number='112', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='112|999', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:0[01348]|1(?:[02]|1[128]|311)|2(?:0[125]|[13-6]|2\\d{0,2})|(?:3[1-35-79]|7[45])\\d\\d?|5(?:454|5\\d\\d?|77|888|999?)|8(?:18?|2|8[18])|9(?:[124]\\d?|68|71|9[0679]))|66628|99[1-469]|13[5-7]|(?:1(?:0[569]|309|5[12]|7[136-9]|9[03])|3[23679]\\d\\d)\\d', example_number='100', possible_length=(3, 4, 5)),
    standard_rate=PhoneNumberDesc(national_number_pattern='666\\d\\d', example_number='66600', possible_length=(5,)),
    sms_services=PhoneNumberDesc(national_number_pattern='(?:3[23679]\\d|666)\\d\\d', example_number='32000', possible_length=(5,)),
    short_data=True)
