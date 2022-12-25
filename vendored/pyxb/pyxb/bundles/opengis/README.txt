This directory adds many of the Geographic Information Systems XML schemas
from http://www.opengeospatial.org/ to PyXB as a bundle.

There are over 800 schemas in the OpenGIS domain, with extremely complex
interrelationships between them.  Translating them is a complex activity,
and the resulting bindings and archive files require over 100MB of disk
space (including the schemas).  As such, bindings are no longer provided in
the PyXB distribution.

You can generate the bindings by setting the PYXB_ROOT environment variable
to the root directory of PyXB (the one in which "setup.py" is found), and
running::

  cd ${PYXB_ROOT}
  maintainer/genbundles @
  pyxb/bundles/opengis/scripts/genbind
  python setup.py install

The genbundles invocation will first generate the standard dependencies
including W3C versions of namespaces formerly provided by OpenGIS.  Then
the opengis genbind script wlil download the latest set of schema from
OpenGIS and translate many of the standards.  The final step installs
the whole system including the new bindings.  The namespaces that are
currently supported by PyXB are listed at
http://pyxb.sourceforge.net/bundles.html#opengis.  Additional namespaces
can be added by modifying the opengis genbind script to include them,
and re-running the script.
