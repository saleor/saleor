from setuptools import setup

setup(
    name="provinces-plugin",
    entry_points={
        "saleor.plugins": [
            "saleor.plugins.provinces = saleor.plugins.provinces.plugin:ProvincesPlugin"
        ]
    },
)
