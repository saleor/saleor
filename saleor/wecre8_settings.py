from saleor.settings import *

LANGUAGES = [
    ("ar", "Arabic"),
    ("en", "English"),
]

PLUGINS.append(
    "saleor.plugins.algolia.plugin.AlgoliaPlugin",
)
