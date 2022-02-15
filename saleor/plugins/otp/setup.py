from setuptools import setup

setup(
    name="otp",
    entry_points={
        "saleor.plugins": ["saleor.plugins.otp = saleor.plugins.otp.plugin:OTPPlugin"]
    },
)
