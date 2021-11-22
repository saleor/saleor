from saleor.settings import *  # noqa F403

LANGUAGES = [
    ("ar", "Arabic"),
    ("en", "English"),
]

PLUGINS.append(  # noqa F403
    "saleor.plugins.algolia.plugin.AlgoliaPlugin",
)
