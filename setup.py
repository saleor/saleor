#! /usr/bin/env python
from setuptools import setup, find_packages
from saleor import version


REQUIREMENTS = [
    'Django == 1.5c1',
    'South >= 0.7.6',
]

setup(name='saleor',
      author='Mirumee Software',
      author_email='hello@mirumee.com',
      description="A fork'n'play e-commerence in Django",
      license='BSD',
      version=version,
      url='http://getsaleor.com/',
      packages=find_packages(where='saleor'),
      include_package_data=True,
      install_requires=REQUIREMENTS,
      dependency_links=['http://github.com/django/django/tarball/1.5c1#egg=Django-1.5c1'],
      entry_points={
          'console_scripts': [
              'saleor = saleor:manage'
          ]
      },
      )
