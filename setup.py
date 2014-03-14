#! /usr/bin/env python
from setuptools import setup, find_packages, Command
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saleor.settings')


class Command(Command):
    user_options = []
    initialize_options = lambda self: None
    finalize_options = lambda self: None


class PopulateDatabase(Command):
    description = "Populate database with test objects"

    def run(self):
        from django.core.management import call_command
        from utils.create_random_data import create_items
        call_command('syncdb', interactive=True, migrate_all=True)
        create_items('saleor/static/placeholders/', 10)


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
        'Django>=1.6',
        'django-images>=0.4,<0.5a0',
        'django-mptt>=0.5',
        'django-payments>=0.4,<0.5a0',
        'django-prices>=0.3,<0.4a0',
        'google-measurement-protocol>=0.1.2,<0.2a0',
        'prices>=0.5,<0.6a0',
        'satchless>=1.1.2,<1.2a0',
        'South>=0.7.6',
        'requests>=1.2.0',
        'unidecode',
        'django-selectable==0.8.0',
        'fake-factory>=0.3.2'
    ],
    entry_points={
        'console_scripts': ['saleor = saleor:manage']},
    tests_require=[
        'mock==1.0.1',
        'purl>=0.4.1',
    ],
    test_suite='saleor.tests.suite',
    cmdclass={
        'populatedb': PopulateDatabase
    }
)
