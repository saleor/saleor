"""
SymPy is a Python library for symbolic mathematics. It aims to become a
full-featured computer algebra system (CAS) while keeping the code as simple
as possible in order to be comprehensible and easily extensible.  SymPy is
written entirely in Python. It depends on mpmath, and other external libraries
may be optionally for things like plotting support.

See the webpage for more information and documentation:

    https://sympy.org

"""


from __future__ import absolute_import, print_function
del absolute_import, print_function

try:
    import mpmath
except ImportError:
    raise ImportError("SymPy now depends on mpmath as an external library. "
    "See https://docs.sympy.org/latest/install.html#mpmath for more information.")

del mpmath

from sympy.release import __version__

if 'dev' in __version__:
    def enable_warnings():
        import warnings
        warnings.filterwarnings('default',   '.*',   DeprecationWarning, module='sympy.*')
        del warnings
    enable_warnings()
    del enable_warnings


import sys
if ((sys.version_info[0] == 2 and sys.version_info[1] < 7) or
    (sys.version_info[0] == 3 and sys.version_info[1] < 4)):
    raise ImportError("Python version 2.7 or 3.4 or above "
                      "is required for SymPy.")

del sys


def __sympy_debug():
    # helper function so we don't import os globally
    import os
    debug_str = os.getenv('SYMPY_DEBUG', 'False')
    if debug_str in ('True', 'False'):
        return eval(debug_str)
    else:
        raise RuntimeError("unrecognized value for SYMPY_DEBUG: %s" %
                           debug_str)
SYMPY_DEBUG = __sympy_debug()

from .core import *
from .logic import *
from .assumptions import *
from .polys import *
from .series import *
from .functions import *
from .ntheory import *
from .concrete import *
from .discrete import *
from .simplify import *
from .sets import *
from .solvers import *
from .matrices import *
from .geometry import *
from .utilities import *
from .integrals import *
from .tensor import *
from .parsing import *
from .calculus import *
from .algebras import *
# This module causes conflicts with other modules:
# from .stats import *
# Adds about .04-.05 seconds of import time
# from combinatorics import *
# This module is slow to import:
#from physics import units
from .plotting import plot, textplot, plot_backends, plot_implicit
from .printing import *
from .interactive import init_session, init_printing

evalf._create_evalf_table()

# This is slow to import:
#import abc

from .deprecated import *
