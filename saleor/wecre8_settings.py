from .settings import *  # noqa

LANGUAGES = [
    ("ar", "Arabic"),
    ("en", "English"),
]

PLUGINS += [  # noqa
    "saleor.plugins.oauth2.plugin.OAuth2Plugin",
]
