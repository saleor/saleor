from setuptools import setup

PLUGIN_PATH = "saleor.plugins.algolia"

setup(
    name="oto",
    entry_points={
        "saleor.plugins": [f"{PLUGIN_PATH} = {PLUGIN_PATH}.plugin:AlgoliaPlugin"],
    },
)
