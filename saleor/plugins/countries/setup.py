from setuptools import setup

setup(
    name="countries-plugin",
    entry_points={
        "saleor.plugins": [
            "saleor.plugins.countries = saleor.plugins.countries.plugin:CountriesPlugin"
        ]
    },
)
