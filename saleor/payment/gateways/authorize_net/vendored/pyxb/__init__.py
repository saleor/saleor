# -*- coding: utf-8 -*-

"""PyXB stands for Python U{W3C XML
Schema<http://www.w3.org/XML/Schema>} Bindings, and is pronounced
"pixbee".  It enables translation between XML instance documents and
Python objects following rules specified by an XML Schema document.

This is the top-level entrypoint to the PyXB system.  Importing this
gets you all the L{exceptions<pyxb.exceptions_.PyXBException>}, and
L{pyxb.namespace}.  For more functionality, delve into these
submodules:

 - L{pyxb.xmlschema} Module holding the
   L{structures<pyxb.xmlschema.structures>} that convert XMLSchema
   from a DOM model to a Python class model based on the XMLSchema
   components.  Use this when you need to operate on the component
   model.

 - L{pyxb.binding} Module used to generate the bindings and at runtime
   to support the generated bindings.  Use this if you need to use the
   binding model or content model.

 - L{pyxb.utils} Common utilities used in parsing, generating, and
   executing.  The submodules must be imported separately.

"""

import logging
from pyxb.utils import six

_log = logging.getLogger(__name__)

class cscRoot (object):
    """This little bundle of joy exists because in Python 2.6 it
    became an error to invoke C{object.__init__} with parameters (unless
    you also override C{__new__}, in which case it's only a warning.
    Whatever.).  Since I'm bloody not going to check in every class
    whether C{super(Myclass,self)} refers to C{object} (even if I could
    figure out how to do that, 'cuz the obvious solutions don't work),
    we'll just make this thing the root of all U{cooperative super
    calling<http://www.geocities.com/foetsch/python/new_style_classes.htm#super>}
    hierarchies.  The standard syntax in PyXB for this pattern is::

      def method_csc (self, *args, **kw):
        self_fn = lambda *_args, **_kw: self
        super_fn = getattr(super(ThisClass, self), 'method_csc', self_fn)
        return super_fn(*args, **kw)

    """

    def __init__ (self, *args, **kw):
        # Oh gross.  If this class descends from list (and probably dict), we
        # get here when object is *not* our direct superclass.  In that case,
        # we have to pass the arguments on up, or the strings don't get
        # created right.  Below is the only way I've figured out to detect the
        # situation.
        #
        # Note that we might also get here if you mix-in a class that used
        # object as a parent instead of cscRoot.  Don't do that.  Printing the
        # mro() is a decent way of identifying the problem.
        if issubclass(self.__class__.mro()[-2], ( list, dict )):
            super(cscRoot, self).__init__(*args)

__version__ = '1.2.5'
"""The version of PyXB"""

__url__ = 'http://pyxb.sourceforge.net'
"""The URL for PyXB's homepage"""

__license__ = 'Apache License 2.0'

# Bring in the exception hierarchy
from pyxb.exceptions_ import *

# Bring in namespace stuff
import pyxb.namespace

class BIND (object):
    """Bundle data for automated binding generation.

    Instances of this class capture positional and keyword arguments that are
    used to create binding instances based on context.  For example, if C{w}
    is an instance of a complex type whose C{option} element is declared to be
    an anonymous class with simple content of type integer and an attribute of
    C{units}, a correct assignment to that element could be achieved with::

      w.option = BIND(54, units="m")

    """
    __args = None
    __kw = None

    def __init__ (self, *args, **kw):
        """Cache parameters for subsequent binding creation.
        Invoke just as you would the factory for a binding class."""
        self.__args = args
        self.__kw = kw

    def createInstance (self, factory, **kw):
        """Invoke the given factory method.

        Position arguments to the factory are those cached in this instance.
        Keyword arguments are the ones on the command line, updated from the
        ones in this instance."""
        kw.update(self.__kw)
        return factory(*self.__args, **kw)


XMLStyle_minidom = 0
"""Use xml.dom.minidom for XML processing.  This is the fastest, but does not
provide location information.  It produces DOM instances."""

XMLStyle_saxdom = 1
"""Use pyxb.utils.saxdom for XML processing.  This is the slowest, but both
provides location information and generates a DOM instance."""

XMLStyle_saxer = 2
"""Use pyxb.binding.saxer when converting documents to binding instances.
This style supports location information in the bindings.  It produces binding
instances directly, without going through a DOM stage, so is faster than
XMLStyle_saxdom.  However, since the pyxb.xmlschema.structures classes require
a DOM model, XMLStyle_saxdom will be used for pyxb.utils.domutils.StringToDOM
if this style is selected."""

_XMLStyle = XMLStyle_saxer
"""The current XML processing style."""

_XMLStyleMap = { 'minidom' : XMLStyle_minidom,
                 'saxdom' : XMLStyle_saxdom,
                 'saxer' : XMLStyle_saxer }
_XMLStyleMapReverse = dict([ (_v, _k) for (_k, _v) in six.iteritems(_XMLStyleMap) ])

_XMLStyle_envvar = 'PYXB_XML_STYLE'

def _SetXMLStyle (style=None):
    """Set the interface used to parse XML content.

    This can be invoked within code.  The system default of L{XMLStyle_saxer}
    can also be overridden at runtime by setting the environment variable
    C{PYXB_XML_STYLE} to one of C{minidom}, C{saxdom}, or C{saxer}.

    @param style: One of L{XMLStyle_minidom}, L{XMLStyle_saxdom},
    L{XMLStyle_saxer}.  If not provided, the system default is used.
    """
    global _XMLStyle
    if style is None:
        import os
        style_name = os.environ.get(_XMLStyle_envvar)
        if style_name is None:
            style_name = 'saxer'
        style = _XMLStyleMap.get(style_name)
        if style is None:
            raise PyXBException('Bad value "%s" for %s' % (style_name, _XMLStyle_envvar))
    if _XMLStyleMapReverse.get(style) is None:
        raise PyXBException('Bad value %s for _SetXMLStyle' % (style,))
    _XMLStyle = style

_SetXMLStyle()

# Global flag that we can use to determine whether optimization is active in
# this session.  There may be cases where we can bypass methods that just
# check for things we don't care about in an optimized context
_OptimizationActive = False
try:
    assert False
    _OptimizationActive = True
except:
    pass

_CorruptionDetectionEnabled = not _OptimizationActive
"""If C{True}, blocks attempts to assign to attributes that are reserved for
PyXB methods.

Applies only at compilation time; dynamic changes are ignored.
"""

class ValidationConfig (object):
    """Class holding configuration related to validation.

    L{pyxb.GlobalValidationConfig} is available to influence validation in all
    contexts.  Each binding class has a reference to an instance of this
    class, which can be inspected using
    L{pyxb.binding.basis._TypeBinding_mixin._GetValidationConfig} and changed
    using L{pyxb.binding.basis._TypeBinding_mixin._SetValidationConfig}.  Each
    binding instance has a reference inherited from its class which can be
    inspected using L{pyxb.binding.basis._TypeBinding_mixin._validationConfig}
    and changed using
    L{pyxb.binding.basis._TypeBinding_mixin._setValidationConfig}.

    This allows fine control on a per class and per-instance basis.

    L{forBinding} replaces L{RequireValidWhenParsing}.

    L{forDocument} replaces L{RequireValidWhenGenerating}.

    L{contentInfluencesGeneration}, L{orphanElementInContent}, and
    L{invalidElementInContent} control how
    L{pyxb.binding.basis.complexTypeDefinition.orderedContent} affects
    generated documents.
    """

    __forBinding = True
    def _getForBinding (self):
        """C{True} iff validation should be performed when manipulating a
        binding instance.

        This includes parsing a document or DOM tree, using a binding instance
        class constructor, or assigning to an element or attribute field of a
        binding instance."""
        return self.__forBinding
    def _setForBinding (self, value):
        """Configure whether validation should be performed when manipulating
        a binding instance."""
        if not isinstance(value, bool):
            raise TypeError(value)
        self.__forBinding = value
        return value
    forBinding = property(_getForBinding)

    __forDocument = True
    def _getForDocument (self):
        """C{True} iff validation should be performed when creating a document
        from a binding instance.

        This applies at invocation of
        L{toDOM()<pyxb.binding.basis._TypeBinding_mixin.toDOM>}.
        L{toxml()<pyxb.binding.basis._TypeBinding_mixin.toDOM>} invokes C{toDOM()}."""
        return self.__forDocument
    def _setForDocument (self, value):
        """Configure whether validation should be performed when generating
        a document from a binding instance."""
        if not isinstance(value, bool):
            raise TypeError(value)
        self.__forDocument = value
        return value
    forDocument = property(_getForDocument)

    ALWAYS = -1
    """Always do it."""

    NEVER = 0
    """Never do it."""

    IGNORE_ONCE = 1
    """If an error occurs ignore it and continue with the next one.  (E.g., if
    an element in a content list fails skip it and continue with the next
    element in the list.)"""

    GIVE_UP = 2
    """If an error occurs ignore it and stop using whatever provided the cause
    of the error.  (E.g., if an element in a content list fails stop
    processing the content list and execute as though it was absent)."""

    RAISE_EXCEPTION = 3
    """If an error occurs, raise an exception."""

    MIXED_ONLY = 4
    """Only when content type is mixed."""

    __contentInfluencesGeneration = MIXED_ONLY
    def __getContentInfluencesGeneration (self):
        """Determine whether complex type content influences element order in
        document generation.

        The value is one of L{ALWAYS}, L{NEVER}, L{MIXED_ONLY} (default)."""
        return self.__contentInfluencesGeneration
    def _setContentInfluencesGeneration (self, value):
        """Set the value of L{contentInfluencesGeneration}."""
        if not (value in ( self.ALWAYS, self.NEVER, self.MIXED_ONLY )):
            raise ValueError(value)
        self.__contentInfluencesGeneration = value
    contentInfluencesGeneration = property(__getContentInfluencesGeneration)

    __orphanElementInContent = IGNORE_ONCE
    def __getOrphanElementInContent (self):
        """How to handle unrecognized elements in content lists.

        This is used when consulting a complex type instance content list to
        influence the generation of documents from a binding instance.

        The value is one of L{IGNORE_ONCE} (default), L{GIVE_UP},
        L{RAISE_EXCEPTION}."""
        return self.__orphanElementInContent
    def _setOrphanElementInContent (self, value):
        """Set the value of L{orphanElementInContent}."""
        if not (value in ( self.IGNORE_ONCE, self.GIVE_UP, self.RAISE_EXCEPTION )):
            raise ValueError(value)
        self.__orphanElementInContent = value
    orphanElementInContent = property(__getOrphanElementInContent)

    __invalidElementInContent = IGNORE_ONCE
    def __getInvalidElementInContent (self):
        """How to handle invalid elements in content lists.

        The value is one of L{IGNORE_ONCE} (default), L{GIVE_UP},
        L{RAISE_EXCEPTION}."""
        return self.__invalidElementInContent
    def _setInvalidElementInContent (self, value):
        """Set the value of L{invalidElementInContent}."""
        if not (value in ( self.IGNORE_ONCE, self.GIVE_UP, self.RAISE_EXCEPTION )):
            raise ValueError(value)
        self.__invalidElementInContent = value
    invalidElementInContent = property(__getInvalidElementInContent)

    def copy (self):
        """Make a copy of this instance.

        Use this to get a starting point when you need to customize validation
        on a per-instance/per-class basis."""
        import copy
        return copy.copy(self)

GlobalValidationConfig = ValidationConfig()

_GenerationRequiresValid = True
"""Legacy flag; prefer L{forDocument<ValidationConfig.forDocument>} in L{GlobalValidationConfig}."""

def RequireValidWhenGenerating (value=None):
    """Query or set a flag that controls validation checking in XML generation.

    Normally any attempts to convert a binding instance to a DOM or XML
    representation requires that the binding validate against the content
    model, since only in this way can the content be generated in the correct
    order.  In some cases it may be necessary or useful to generate a document
    from a binding that is incomplete.  If validation is not required, the
    generated documents may not validate even if the content validates,
    because ordering constraints will be ignored.

    @keyword value: If absent or C{None}, no change is made; otherwise, this
    enables (C{True}) or disables (C{False}) the requirement that instances
    validate before being converted to XML.
    @type value: C{bool}

    @return: C{True} iff attempts to generate XML for a binding that does not
    validate should raise an exception.  """
    if value is None:
        return GlobalValidationConfig.forDocument
    global _GenerationRequiresValid
    _GenerationRequiresValid = GlobalValidationConfig._setForDocument(value)
    return value

_ParsingRequiresValid = True
"""Legacy flag; prefer L{forBinding<ValidationConfig.forBinding>} in L{GlobalValidationConfig}."""
def RequireValidWhenParsing (value=None):
    """Query or set a flag that controls validation checking in XML parsing.

    Normally any attempts to convert XML to a binding instance to a binding
    instance requires that the document validate against the content model.
    In some cases it may be necessary or useful to process a document that is
    incomplete.  If validation is not required, the generated documents may
    not validate even if the content validates, because ordering constraints
    will be ignored.

    @keyword value: If absent or C{None}, no change is made; otherwise, this
    enables (C{True}) or disables (C{False}) the requirement that documents
    validate when being converted to bindings.
    @type value: C{bool}

    @return: C{True} iff attempts to generate bindings for a document that
    does not validate should raise an exception."""
    if value is None:
        return GlobalValidationConfig.forBinding
    global _ParsingRequiresValid
    _ParsingRequiresValid = GlobalValidationConfig._setForBinding(value)
    return _ParsingRequiresValid

_PreserveInputTimeZone = False
def PreserveInputTimeZone (value=None):
    """Control whether time values are converted to UTC during input.

    The U{specification <http://www.w3.org/TR/xmlschema-2/#dateTime>} makes
    clear that timezoned times are in UTC and that times in other timezones
    are to be translated to UTC when converted from literal to value form.
    Provide an option to bypass this step, so the input timezone is preserved.

    @note: Naive processing of unnormalized times--i.e., ignoring the
    C{tzinfo} field--may result in errors."""
    global _PreserveInputTimeZone
    if value is None:
        return _PreserveInputTimeZone
    if not isinstance(value, bool):
        raise TypeError(value)
    _PreserveInputTimeZone = value
    return _PreserveInputTimeZone

_OutputEncoding = 'utf-8'
"""Default unicode encoding to use when creating output.

Material being written to an XML parser is not output."""

_InputEncoding = 'utf-8'
"""Default unicode encoding to assume when decoding input.

Material being written to an XML parser is treated as input."""

def NonElementContent (instance):
    """Return an iterator producing the non-element content of the provided instance.

    The catenated text of the non-element content of an instance can
    be obtained with::

       text = six.u('').join(pyxb.NonElementContent(instance))

    @param instance: An instance of L{pyxb.binding.basis.complexTypeDefinition}.

    @return: an iterator producing text values
    """
    import pyxb.binding.basis
    return pyxb.binding.basis.NonElementContent.ContentIterator(instance.orderedContent())

## Local Variables:
## fill-column:78
## End:
