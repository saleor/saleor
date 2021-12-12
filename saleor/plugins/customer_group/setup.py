from setuptools import setup

# making two gloable var for passing the flake8 lint
plugin_name = "saleor.plugins.customer_group"
plugin_name_path = "saleor.plugins.customer_group.plugin:CustomerGroupPlugin"

saleor_plugin = f"{plugin_name} = {plugin_name_path}"
setup(
    name="customer_group",
    entry_points={"saleor.plugins": [saleor_plugin]},
)
