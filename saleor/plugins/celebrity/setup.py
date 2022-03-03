from setuptools import setup

plugin_name = "saleor.plugins.celebrity"
plugin_name_path = "saleor.plugins.celebrity.plugin:CelebrityPlugin"

saleor_plugin = f"{plugin_name} = {plugin_name_path}"
setup(
    name="celebrity",
    entry_points={"saleor.plugins": [saleor_plugin]},
)
