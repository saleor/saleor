from ..core.utils import delete_versatile_image


def delete_avatar(sender, instance, **kwargs):
    if avatar := instance.avatar:
        delete_versatile_image(avatar)
