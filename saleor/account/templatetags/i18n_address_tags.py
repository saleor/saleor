import i18naddress
from django import template
from django.utils.translation import pgettext

register = template.Library()


@register.inclusion_tag("formatted_address.html")
def format_address(address, include_phone=True, inline=False, latin=False):
    address_data = address.as_data()
    address_data["name"] = (
        pgettext("Address data", "%(first_name)s %(last_name)s") % address_data
    )
    address_data["country_code"] = address_data["country"]
    address_data["street_address"] = pgettext(
        "Address data", "%(street_address_1)s\n" "%(street_address_2)s" % address_data
    )
    address_lines = i18naddress.format_address(address_data, latin).split("\n")
    if include_phone and address.phone:
        address_lines.append(address.phone)
    return {"address_lines": address_lines, "inline": inline}
