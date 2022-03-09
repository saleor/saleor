from setuptools import setup

plugin_name = "saleor.plugins.wishlist"
plugin_name_path = "saleor.plugins.wishlist.plugin:WishlistPlugin"

saleor_plugin = f"{plugin_name} = {plugin_name_path}"
setup(
    name="wishlist",
    entry_points={"saleor.plugins": [saleor_plugin]},
)
