from setuptools import setup

setup(
    name="customer_group",
    entry_points={
        "saleor.plugins": [
            "saleor.plugins.customer_group = saleor.plugins.customer_group.plugin:CustomerGroupPlugin"
        ]
    },
)
