from setuptools import setup

setup(
    name="oauth2",
    entry_points={"saleor.plugins": ["oauth2 = oauth2.plugin:OAuth2Plugin"]},
)
