#! /usr/bin/env python
import os
from setuptools import setup, find_packages, Command
from setuptools.command import easy_install
from saleor import version


REQUIREMENTS = [
    'Django == 1.5c1',
    'South >= 0.7.6',
    'satchless',
]

DEVELOPMENT_DEPENDECIES = [
    'https://github.com/lamby/django-lint/archive/55290d.zip',
    'pylint==0.26.0',
]


class DevelopmentDependecies(Command):
    user_options = []
    initialize_options = lambda self: None
    finalize_options = lambda self: None

    def run(self):
        easy_install.main(DEVELOPMENT_DEPENDECIES)

setup(name='saleor',
      author='Mirumee Software',
      author_email='hello@mirumee.com',
      description="A fork'n'play e-commerence in Django",
      license='BSD',
      version=version,
      url='http://getsaleor.com/',
      packages=find_packages(),
      include_package_data=True,
      install_requires=REQUIREMENTS,
      dependency_links=[
          'http://github.com/django/django/tarball/1.5c1#egg=Django-1.5c1',
          'http://github.com/mirumee/satchless/tarball/master#egg=satchless',
      ],
      entry_points={
          'console_scripts': [
              'saleor = saleor:manage'
          ]
      },
      cmdclass={'development_dependecies': DevelopmentDependecies},
      )
