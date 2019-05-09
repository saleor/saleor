from __future__ import print_function, division

from sympy.printing.mathml import mathml
import tempfile
import os


def print_gtk(x, start_viewer=True):
    """Print to Gtkmathview, a gtk widget capable of rendering MathML.

    Needs libgtkmathview-bin
    """
    from sympy.utilities.mathml import c2p

    tmp = tempfile.mkstemp()  # create a temp file to store the result
    with open(tmp, 'wb') as file:
        file.write(c2p(mathml(x), simple=True))

    if start_viewer:
        os.system("mathmlviewer " + tmp)
