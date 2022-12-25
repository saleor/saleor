#!/usr/bin/env python

from __future__ import print_function
import sys

# The current version of the system.  Format is #.#.#[-DEV].
version = '1.2.5'

# Require Python 2.6 or higher or Python 3.1 or higher
if (sys.version_info[:2] < (2, 6)) or ((sys.version_info[0] == 3) and sys.version_info[:2] < (3, 1)):
    raise ValueError('''PyXB requires:
  Python2 version 2.6 or later; or
  Python3 version 3.1 or later
(You have %s.)''' % (sys.version,))

import os
import stat
import re
import datetime
import logging

from distutils.core import setup, Command

# Stupid little command to automatically update the version number
# where it needs to be updated.
class update_version (Command):
    # Brief (40-50 characters) description of the command
    description = "Substitute @VERSION@ in relevant files"

    # List of option tuples: long name, short name (None if no short
    # name), and help string.
    user_options = [ ]
    boolean_options = [ ]

    # Files in the distribution that need to be rewritten when the
    # version number changes
    files = ( 'README.txt', 'pyxb/__init__.py', 'doc/conf.py' )

    # The substitutions (key braced by @ signs)
    substitutions = { 'VERSION' : version,
                      'THIS_YEAR' : datetime.date.today().strftime('%Y'),
                      'SHORTVERSION' : '.'.join(version.split('.')[:2]) }

    def initialize_options (self):
        pass

    def finalize_options (self):
        pass

    def run (self):
        for f in self.files:
            text = open('%s.in' % (f,)).read()
            for (k, v) in self.substitutions.items():
                text = text.replace('@%s@' % (k,), v)
            os.chmod(f, os.stat(f)[stat.ST_MODE] | stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
            open(f,'w').write(text)
            os.chmod(f, os.stat(f)[stat.ST_MODE] & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))

class test (Command):

    # Brief (40-50 characters) description of the command
    description = "Run all unit tests found in testdirs"

    # List of option tuples: long name, short name (None if no short
    # name), and help string.
    user_options = [ ( 'testdirs=', None, 'colon separated list of directories to search for tests' ),
                     ( 'trace-tests', 'v', 'trace search for tests' ),
                     ( 'inhibit-output', 'q', 'inhibit test output' ),
                     ]
    boolean_options = [ 'trace-tests', 'inhibit-output' ]

    def initialize_options (self):
        self.trace_tests = None
        self.inhibit_output = None
        self.testdirs = 'tests'

    def finalize_options (self):
        pass

    # Regular expression that matches unittest sources
    __TestFile_re = re.compile(r'^test.*\.py$')

    def run (self):
        # Make sure log messages are supported
        logging.basicConfig()

        # Walk the tests hierarchy looking for tests
        dirs = self.testdirs.split(':')
        tests = [ ]
        while dirs:
            dir = dirs.pop(0)
            if self.trace_tests:
                print('Searching for tests in %s' % (dir,))
            for f in os.listdir(dir):
                fn = os.path.join(dir, f)
                statb = os.stat(fn)
                if stat.S_ISDIR(statb[0]):
                    dirs.append(fn)
                elif self.__TestFile_re.match(f):
                    tests.append(fn)

        number = 0
        import sys
        import traceback
        import unittest
        import types

        # Import each test into its own module, then add the test
        # cases in it to a complete suite.
        loader = unittest.defaultTestLoader
        suite = unittest.TestSuite()
        used_names = set()
        for fn in tests:
            stage = 'compile'
            try:
                # Assign a unique name for this test
                test_name = os.path.basename(fn).split('.')[0]
                test_name = test_name.replace('-', '_')
                number = 2
                base_name = test_name
                while test_name in used_names:
                    test_name = '%s%d' % (base_name, number)
                    number += 1

                # Read the test source in and compile it
                rv = compile(open(fn).read(), test_name, 'exec')
                state = 'evaluate'

                # Make a copy of the globals array so we don't
                # contaminate this environment.
                g = globals().copy()

                # The test cases use __file__ to determine the path to
                # the schemas
                g['__file__'] = fn

                # Create a module into which the test will be evaluated.
                module = types.ModuleType(test_name)

                # The generated code uses __name__ to look up the
                # containing module in sys.modules.
                g['__name__'] = test_name
                sys.modules[test_name] = module

                # Import the test into the module, making sure the created globals look like they're in the module.
                eval(rv, g)
                module.__dict__.update(g)

                # Find all subclasses of unittest.TestCase that were
                # in the test source and add them to the suite.
                for (nm, obj) in g.items():
                    if (type == type(obj)) and issubclass(obj, unittest.TestCase):
                        suite.addTest(loader.loadTestsFromTestCase(obj))
                if self.trace_tests:
                    print('%s imported' % (fn,))
            except Exception as e:
                print('%s failed in %s: %s' % (fn, stage, e))
                raise

        # Run everything
        verbosity = 1
        if self.trace_tests:
            verbosity = 2
        elif self.inhibit_output:
            # Don't know how to do this for real
            verbosity = 0
        runner = unittest.TextTestRunner(verbosity=verbosity)
        runner.run(suite)

import glob
import sys
import pyxb.utils.utility

packages = [
        'pyxb', 'pyxb.namespace', 'pyxb.binding', 'pyxb.utils', 'pyxb.xmlschema',
        "pyxb.bundles"
        ]
package_data = {}

init_re = re.compile(r'^__init__\.py$')
wxs_re = re.compile(r'^.*\.wxs$')

setup_path = os.path.dirname(__file__)
bundle_base = os.path.join(setup_path, 'pyxb', 'bundles')
possible_bundles = []
try:
    possible_bundles.extend(os.listdir(bundle_base))
except OSError as e:
    print("Directory %s bundle search failed: %s" % (bundle_base, e))
for possible_bundle in possible_bundles:
    bundle_root = os.path.join(bundle_base, possible_bundle)
    if not os.path.isdir(bundle_root):
        continue
    b_packages = []
    b_data = { }
    for fp in pyxb.utils.utility.GetMatchingFiles('%s//' % (bundle_root,), init_re):
        bundle_path = os.path.dirname(os.path.normpath(fp))
        try:
            package_relpath = os.path.relpath(bundle_path, setup_path)
        except AttributeError as e:
            package_relpath = bundle_path
            if setup_path and '.' != setup_path:
                prefix_path = setup_path + os.path.sep
                if not package_relpath.startswith(prefix_path):
                    print("Unable to determine relative path from %s to %s installation" % (setup_path, bundle_path))
                    sys.exit(1)
                package_relpath = package_relpath[len(prefix_path):]
        package = package_relpath.replace(os.path.sep, '.')
        b_packages.append(package)
        wxs_files = [os.path.basename(_f) for _f in pyxb.utils.utility.GetMatchingFiles(bundle_path, wxs_re) ]
        if wxs_files:
            b_data[package] = wxs_files
    if 0 < len(b_data):
        print('Found bundle in %s' % (bundle_root,))
        packages.extend(b_packages)
        package_data.update(b_data)

setup(name='PyXB',
      description = 'PyXB ("pixbee") is a pure Python package that generates Python source code for classes that correspond to data structures defined by XMLSchema.',
      author='Peter A. Bigot',
      author_email='pabigot@users.sourceforge.net',
      url='http://pyxb.sourceforge.net',
      # Also change in README.TXT, pyxb/__init__.py, and doc/conf.py
      version=version,
      license='Apache License 2.0',
      long_description='''PyXB is a pure `Python <http://www.python.org>`_ package that generates
Python code for classes that correspond to data structures defined by
`XMLSchema <http://www.w3.org/XML/Schema>`_.  In concept it is similar to
`JAXB <http://en.wikipedia.org/wiki/JAXB>`_ for Java and `CodeSynthesis XSD
<http://www.codesynthesis.com/products/xsd/>`_ for C++.

The major goals of PyXB are:

* Provide a generated Python interface that is "Pythonic", meaning similar
  to one that would have been hand-written:

  + Attributes and elements are Python properties, with name conflicts
    resolved in favor of elements
  + Elements with maxOccurs larger than 1 are stored as Python lists
  + Bindings for type extensions inherit from the binding for the base type
  + Enumeration constraints are exposed as class (constant) variables

* Support bi-directional conversion (document to Python and back)

* Allow easy customization of the generated bindings to provide
  functionality along with content

* Support all XMLSchema features that are in common use, including:

  + complex content models (nested all/choice/sequence)
  + cross-namespace dependencies
  + include and import directives
  + constraints on simple types
''',
      provides=[ 'PyXB' ],
      packages=packages,
      package_data=package_data,
      # I normally keep these in $purelib, but distutils won't tell me where that is.
      # We don't need them in the installation anyway.
      #data_files= [ ('pyxb/standard/schemas', glob.glob(os.path.join(*'pyxb/standard/schemas/*.xsd'.split('/'))) ) ],
      scripts=[ 'scripts/pyxbgen', 'scripts/pyxbwsdl', 'scripts/pyxbdump' ],
      cmdclass = { 'test' : test,
                   'update_version' : update_version },
      classifiers = [ 'Development Status :: 5 - Production/Stable'
                      , 'Intended Audience :: Developers'
                      , 'License :: OSI Approved :: Apache Software License'
                      , 'Topic :: Software Development :: Code Generators'
                      , 'Topic :: Text Processing :: Markup :: XML'
                      , 'Programming Language :: Python :: 2'
                      , 'Programming Language :: Python :: 2.6'
                      , 'Programming Language :: Python :: 2.7'
                      , 'Programming Language :: Python :: 3'
                      # Skip 3.0 because it doesn't know how to be built with hashlib support
                      , 'Programming Language :: Python :: 3.1'
                      , 'Programming Language :: Python :: 3.2'
                      , 'Programming Language :: Python :: 3.3'
                      , 'Programming Language :: Python :: 3.4'
                      ] )
