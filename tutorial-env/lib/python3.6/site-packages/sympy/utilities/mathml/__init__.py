"""Module with some functions for MathML, like transforming MathML
content in MathML presentation.

To use this module, you will need lxml.
"""

from sympy.utilities.pkgdata import get_resource
from sympy.utilities.decorator import doctest_depends_on
import xml.dom.minidom


__doctest_requires__ = {('apply_xsl', 'c2p'): ['lxml']}


def add_mathml_headers(s):
    return """<math xmlns:mml="http://www.w3.org/1998/Math/MathML"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://www.w3.org/1998/Math/MathML
        http://www.w3.org/Math/XMLSchema/mathml2/mathml2.xsd">""" + s + "</math>"


@doctest_depends_on(modules=('lxml',))
def apply_xsl(mml, xsl):
    """Apply a xsl to a MathML string
    @param mml: a string with MathML code
    @param xsl: a string representing a path to a xsl (xml stylesheet)
        file. This file name is relative to the PYTHONPATH

    >>> from sympy.utilities.mathml import apply_xsl
    >>> xsl = 'mathml/data/simple_mmlctop.xsl'
    >>> mml = '<apply> <plus/> <ci>a</ci> <ci>b</ci> </apply>'
    >>> res = apply_xsl(mml,xsl)
    >>> ''.join(res.splitlines())
    '<?xml version="1.0"?><mrow xmlns="http://www.w3.org/1998/Math/MathML">  <mi>a</mi>  <mo> + </mo>  <mi>b</mi></mrow>'

    """
    from lxml import etree
    s = etree.XML(get_resource(xsl).read())
    transform = etree.XSLT(s)
    doc = etree.XML(mml)
    result = transform(doc)
    s = str(result)
    return s


@doctest_depends_on(modules=('lxml',))
def c2p(mml, simple=False):
    """Transforms a document in MathML content (like the one that sympy produces)
    in one document in MathML presentation, more suitable for printing, and more
    widely accepted

    >>> from sympy.utilities.mathml import c2p
    >>> mml = '<apply> <exp/> <cn>2</cn> </apply>'
    >>> c2p(mml,simple=True) != c2p(mml,simple=False)
    True

    """

    if not mml.startswith('<math'):
        mml = add_mathml_headers(mml)

    if simple:
        return apply_xsl(mml, 'mathml/data/simple_mmlctop.xsl')

    return apply_xsl(mml, 'mathml/data/mmlctop.xsl')
