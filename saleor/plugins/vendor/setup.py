from setuptools import setup

# making two gloable var for passing the flake8 lint
plugin_name = "saleor.plugins.vendor"
plugin_name_path = "saleor.plugins.vendor.plugin:VendorPlugin"

saleor_plugin = f"{plugin_name} = {plugin_name_path}"
setup(
    name="vendor",
    entry_points={"saleor.plugins": [saleor_plugin]},
)
