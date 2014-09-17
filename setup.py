#! /usr/bin/env python
from setuptools import setup, find_packages, Command
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saleor.settings')

setup(
    name='saleor',
    author='Mirumee Software',
    author_email='hello@mirumee.com',
    description="A fork'n'play e-commerence in Django",
    license='BSD',
    version='0.1.0a0',
    url='http://getsaleor.com/',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Babel>=1.3,<1.4a0',
        'BabelDjango>=0.2,<0.3a0',
        'Django>=1.6',
        'django-images>=0.4,<0.5a0',
        'django-model-utils>=2.0.0,<2.1a0',
        'django-mptt>=0.5',
        'django-payments>=0.5.2,<0.6a0',
        'django-prices>=0.3.3,<0.4a0',
        'django-selectable==0.8.0',
        'fake-factory>=0.3.2',
        'google-measurement-protocol>=0.1.2,<0.2a0',
        'Markdown>=2.4',
        'prices>=0.5,<0.6a0',
        'requests>=1.2.0',
        'satchless>=1.1.2,<1.2a0',
        'unidecode'
    ],
    entry_points={
        'console_scripts': ['saleor = saleor:manage']},
    tests_require=[
        'mock==1.0.1',
        'purl>=0.4.1',
    ],
    test_suite='saleor.tests.suite'
)
