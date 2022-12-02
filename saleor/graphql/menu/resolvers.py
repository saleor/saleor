from ...menu import models
from ..channel import ChannelContext, ChannelQsContext
from ..core.utils import from_global_id_or_error
from ..core.validators import validate_one_of_args_is_in_query
from .types import Menu


def resolve_menu(_info, channel, menu_id=None, name=None, slug=None):
    validate_one_of_args_is_in_query("id", menu_id, "name", name, "slug", slug)
    menu = None
    if menu_id:
        _, id = from_global_id_or_error(menu_id, Menu)
        menu = models.Menu.objects.filter(id=id).first()
    if name:
        menu = models.Menu.objects.filter(name=name).first()
    if slug:
        menu = models.Menu.objects.filter(slug=slug).first()
    return ChannelContext(node=menu, channel_slug=channel) if menu else None


def resolve_menus(_info, channel):
    return ChannelQsContext(qs=models.Menu.objects.all(), channel_slug=channel)


def resolve_menu_item(id, channel):
    menu_item = models.MenuItem.objects.filter(pk=id).first()
    return ChannelContext(node=menu_item, channel_slug=channel) if menu_item else None


def resolve_menu_items(_info):
    return models.MenuItem.objects.all()
