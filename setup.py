#! /usr/bin/env python
from setuptools import setup, find_packages, Command
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'saleor.settings'


class Command(Command):
    user_options = []
    initialize_options = lambda self: None
    finalize_options = lambda self: None


class Lint(Command):
    def run(self):
        import lint
        lint.run()

setup(
    name='saleor',
    author='Mirumee Software',
    author_email='hello@mirumee.com',
    description="A fork'n'play e-commerence in Django",
    license='BSD',
    version='0.1a0',
    url='http://getsaleor.com/',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Django>=1.5',
        'django-mptt>=0.5',
        'django-prices>=0.2,<0.3a0',
        'satchless>=1.0a0,<1.1a0',
        'South>=0.7.6',
        'unidecode',
        'requests>=1.2.0'],
    extras_require={
        'lint': ['pylint==0.26.0', 'django-lint==dev']},
    dependency_links=[
        'http://github.com/mirumee/satchless/tarball/django-removal#egg=satchless-2013.2a',
        'http://github.com/lamby/django-lint/tarball/master#egg=django-lint-dev'],
    entry_points={
        'console_scripts': ['saleor = saleor:manage']},
    cmdclass={
        'lint': Lint},
    tests_require=[
        'mock==1.0.1',
        'discover==0.4.0',
        'purl>=0.4.1'],
    test_suite='discover.collector')
