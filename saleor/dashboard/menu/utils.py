from django.utils.formats import localize
from django.utils.translation import pgettext

from ...page.models import Page


def get_menu_obj_text(obj):
    if isinstance(obj, Page) and obj.is_published and obj.publication_date:
        return pgettext(
            "Menu item page hidden status",
            "%(menu_item_name)s is hidden "
            "(will become visible on %(available_on_date)s)"
            % (
                {
                    "available_on_date": localize(obj.publication_date),
                    "menu_item_name": str(obj),
                }
            ),
        )
    if getattr(obj, "is_published", True):
        return str(obj)
    return pgettext(
        "Menu item published status",
        "%(menu_item_name)s (Not published)" % {"menu_item_name": str(obj)},
    )
