from setuptools import setup

setup(
    name="oauth2",
    entry_points={
        "saleor.plugins": [
            "saleor.plugins.oauth2 = saleor.plugins.oauth2.plugin:OAuth2Plugin"
        ]
    },
)
