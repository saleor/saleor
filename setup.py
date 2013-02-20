#! /usr/bin/env python
from setuptools import setup, find_packages, Command


class Command(Command):
    user_options = []
    initialize_options = lambda self: None
    finalize_options = lambda self: None


class Lint(Command):
    def run(self):
        import lint
        lint.run()


setup(name='saleor',
      author='Mirumee Software',
      author_email='hello@mirumee.com',
      description="A fork'n'play e-commerence in Django",
      license='BSD',
      version='dev',
      url='http://getsaleor.com/',
      packages=find_packages(),
      include_package_data=True,
      install_requires=[
          'Django==1.5c1',
          'South>=0.7.6',
          'satchless',
          'unidecode',
      ],
      extras_require={
          'lint': ['pylint==0.26.0', 'django-lint==dev']
      },
      dependency_links=[
          'http://github.com/django/django/tarball/1.5c1#egg=Django-1.5c1',
          'http://github.com/mirumee/satchless/tarball/master#egg=satchless',
          'http://github.com/lamby/django-lint/tarball/master#egg=django-lint-dev',
      ],
      entry_points={
          'console_scripts': [
              'saleor = saleor:manage'
          ]
      },
      cmdclass={'lint': Lint},
      )
