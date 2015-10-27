#! /usr/bin/env python
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saleor.settings')


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]
    test_args = []

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name='saleor',
    author='Mirumee Software',
    author_email='hello@mirumee.com',
    description="A fork'n'play e-commerce in Django",
    license='BSD',
    version='0.1.0a0',
    url='http://getsaleor.com/',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Babel>=1.3,<1.4a0',
        'BabelDjango>=0.2,<0.3a0',
        'Django>=1.8',
        'dj_database_url>=0.3.0',
        'django-emailit>=0.2.2',
        'django-filter==0.11.0',
        'django-materializecss-form==0.0.64',
        'django-model-utils>=2.0.0,<2.1a0',
        'django-mptt>=0.7.1',
        'django-offsite-storage>=0.0.5',
        'django-payments>=0.7.0,<0.8a0',
        'django-prices>=0.4.0,<0.5a0',
        'djangorestframework>=3.1,<3.2a0',
        'django-selectable==0.8.0',
        'django-versatileimagefield>=1.0.1,<1.1a0',
        'fake-factory>=0.3.2',
        'google-measurement-protocol>=0.1.2,<0.2a0',
        'jsonfield>=1.0.3',
        'Markdown>=2.4',
        'prices>=0.5,<0.6a0',
        'requests>=1.2.0',
        'satchless>=1.1.2,<1.2a0',
        'unidecode'
    ],
    extras_require={
        'PaaS': [
            'whitenoise==1.0.6',
            'gunicorn==19.2.1',
            'psycopg2==2.6']},
    cmdclass={
        'test': PyTest},
    entry_points={
        'console_scripts': ['saleor = saleor:manage']},
    tests_require=[
        'mock==1.3.0',
        'purl>=0.4.1',
        'pytest',
        'pytest-django'])
