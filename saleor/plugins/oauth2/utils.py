from .consts import URI_MAPPING


def get_oauth_info(provider, info):
    plugin = info.context.app

    return plugin.get_oauth2_info(provider)


def get_state_from_qs(info):
    return info.context.GET.get("state")


def get_uri_for(provider, _for):
    return URI_MAPPING[provider][_for]
