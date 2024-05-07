from enum import Enum

from ..graphql.account.enums import CountryCodeEnum


class AddressFieldsToSubstitute(Enum):
    CITY_AREA = "city_area"
    COUNTRY_AREA = "country_area"


IE_COUNTRY_AREA = {
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
IE_COUNTRY_AREA = {k.strip().lower(): v for k, v in IE_COUNTRY_AREA.items()}

VALID_ADDRESS_EXTENSION_MAP: dict[str, dict[str, dict[str, str]]] = {
    CountryCodeEnum.IE.value: {
        AddressFieldsToSubstitute.COUNTRY_AREA.value: IE_COUNTRY_AREA
    }
}
