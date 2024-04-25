from ..graphql.account.enums import CountryCodeEnum


class AddressFieldsToSubstitute:
    CITY = "city"
    CITY_AREA = "city_area"
    COUNTRY_AREA = "country_area"


IE_country_area = {
    "Carlow": "Co. Carlow",
    "Cavan": "Co. Cavan",
    "Clare": "Co. Clare",
    "Cork": "Co. Cork",
    "Donegal": "Co. Donegal",
    "Dublin": "Co. Dublin",
    "Galway": "Co. Galway",
    "Kerry": "Co. Kerry",
    "Kildare": "Co. Kildare",
    "Kilkenny": "Co. Kilkenny",
    "Laois": "Co. Laois",
    "Leitrim": "Co. Leitrim",
    "Limerick": "Co. Limerick",
    "Longford": "Co. Longford",
    "Louth": "Co. Louth",
    "Mayo": "Co. Mayo",
    "Meath": "Co. Meath",
    "Monaghan": "Co. Monaghan",
    "Offaly": "Co. Offaly",
    "Roscommon": "Co. Roscommon",
    "Sligo": "Co. Sligo",
    "Tipperary": "Co. Tipperary",
    "Waterford": "Co. Waterford",
    "Westmeath": "Co. Westmeath",
    "Wexford": "Co. Wexford",
    "Wicklow": "Co. Wicklow",
}

custom_address_names_map = {
    CountryCodeEnum.IE.value: {AddressFieldsToSubstitute.COUNTRY_AREA: IE_country_area}
}
