"""Auto-generated file, do not edit by hand. TH metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_TH = PhoneMetadata(id='TH', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d{2,3}', possible_length=(3, 4)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:1(?:00|2[03]|3[3479]|7[67]|9[0246])|578|6(?:44|6[79]|88|9[16])|88\\d|9[19])|1[15]55', example_number='191', possible_length=(3, 4)),
    premium_rate=PhoneNumberDesc(national_number_pattern='1(?:113|2[23]\\d|5(?:09|56))', example_number='1113', possible_length=(4,)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:669|9[19])', example_number='191', possible_length=(3, 4)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:0[0-2]|1(?:0[03]|1[1-35]|2[0358]|3[03-79]|4[02-489]|5[04-9]|6[04-79]|7[03-9]|8[027-9]|9[02-79])|2(?:22|3[89])|3(?:18|2[23]|3[013]|5[56]|6[45]|73)|477|5(?:0\\d|4[0-37-9]|5[1-8]|6[01679]|7[12568]|8[0-24589]|9[013589])|6(?:0[0-29]|2[03]|4[3-6]|6[1-9]|7[0257-9]|8[0158]|9[014-9])|7(?:[14]9|7[27]|90)|888|9[19])', example_number='100', possible_length=(3, 4)),
    standard_rate=PhoneNumberDesc(national_number_pattern='1(?:1(?:03|1[15]|2[58]|3[056]|4[02-49]|5[046-9]|7[03-589]|9[579])|5(?:0[0-8]|4[0-378]|5[1-478]|7[156])|6(?:20|4[356]|6[1-68]|7[057-9]|8[015]|9[0457-9]))|1(?:1[68]|3[1-35]|5[689]|60|7[17])\\d', example_number='1103', possible_length=(4,)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='114[89]', example_number='1148', possible_length=(4,)),
    short_data=True)
