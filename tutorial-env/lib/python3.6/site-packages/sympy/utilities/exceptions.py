"""
General SymPy exceptions and warnings.
"""

from __future__ import print_function, division

import warnings

from sympy.core.compatibility import string_types
from sympy.utilities.misc import filldedent


class SymPyDeprecationWarning(DeprecationWarning):
    r"""A warning for deprecated features of SymPy.

    This class is expected to be used with the warnings.warn function (note
    that one has to explicitly turn on deprecation warnings):

    >>> import warnings
    >>> from sympy.utilities.exceptions import SymPyDeprecationWarning
    >>> warnings.simplefilter(
    ...     "always", SymPyDeprecationWarning)
    >>> warnings.warn(
    ...     SymPyDeprecationWarning(feature="Old deprecated thing",
    ...     issue=1065, deprecated_since_version="1.0")) #doctest:+SKIP
    __main__:3: SymPyDeprecationWarning:

    Old deprecated thing has been deprecated since SymPy 1.0. See
    https://github.com/sympy/sympy/issues/1065 for more info.

    >>> SymPyDeprecationWarning(feature="Old deprecated thing",
    ... issue=1065, deprecated_since_version="1.1").warn() #doctest:+SKIP
    __main__:1: SymPyDeprecationWarning:

    Old deprecated thing has been deprecated since SymPy 1.1.
    See https://github.com/sympy/sympy/issues/1065 for more info.

    Three arguments to this class are required: ``feature``, ``issue`` and
    ``deprecated_since_version``.

    The ``issue`` flag should be an integer referencing for a "Deprecation
    Removal" issue in the SymPy issue tracker. See
    https://github.com/sympy/sympy/wiki/Deprecating-policy.

    >>> SymPyDeprecationWarning(
    ...    feature="Old feature",
    ...    useinstead="new feature",
    ...    issue=5241,
    ...    deprecated_since_version="1.1")
    Old feature has been deprecated since SymPy 1.1. Use new feature
    instead. See https://github.com/sympy/sympy/issues/5241 for more info.

    Every formal deprecation should have an associated issue in the GitHub
    issue tracker.  All such issues should have the DeprecationRemoval
    tag.

    Additionally, each formal deprecation should mark the first release for
    which it was deprecated.  Use the ``deprecated_since_version`` flag for
    this.

    >>> SymPyDeprecationWarning(
    ...    feature="Old feature",
    ...    useinstead="new feature",
    ...    deprecated_since_version="0.7.2",
    ...    issue=1065)
    Old feature has been deprecated since SymPy 0.7.2. Use new feature
    instead. See https://github.com/sympy/sympy/issues/1065 for more info.

    To provide additional information, create an instance of this
    class in this way:

    >>> SymPyDeprecationWarning(
    ...     feature="Such and such",
    ...     last_supported_version="1.2.3",
    ...     useinstead="this other feature",
    ...     issue=1065,
    ...     deprecated_since_version="1.1")
    Such and such has been deprecated since SymPy 1.1. It will be last
    supported in SymPy version 1.2.3. Use this other feature instead. See
    https://github.com/sympy/sympy/issues/1065 for more info.

    Note that the text in ``feature`` begins a sentence, so if it begins with
    a plain English word, the first letter of that word should be capitalized.

    Either (or both) of the arguments ``last_supported_version`` and
    ``useinstead`` can be omitted. In this case the corresponding sentence
    will not be shown:

    >>> SymPyDeprecationWarning(feature="Such and such",
    ...     useinstead="this other feature", issue=1065,
    ...     deprecated_since_version="1.1")
    Such and such has been deprecated since SymPy 1.1. Use this other
    feature instead. See https://github.com/sympy/sympy/issues/1065 for
    more info.

    You can still provide the argument value.  If it is a string, it
    will be appended to the end of the message:

    >>> SymPyDeprecationWarning(
    ...     feature="Such and such",
    ...     useinstead="this other feature",
    ...     value="Contact the developers for further information.",
    ...     issue=1065,
    ...     deprecated_since_version="1.1")
    Such and such has been deprecated since SymPy 1.1. Use this other
    feature instead. See https://github.com/sympy/sympy/issues/1065 for
    more info.  Contact the developers for further information.

    If, however, the argument value does not hold a string, a string
    representation of the object will be appended to the message:

    >>> SymPyDeprecationWarning(
    ...     feature="Such and such",
    ...     useinstead="this other feature",
    ...     value=[1,2,3],
    ...     issue=1065,
    ...     deprecated_since_version="1.1")
    Such and such has been deprecated since SymPy 1.1. Use this other
    feature instead. See https://github.com/sympy/sympy/issues/1065 for
    more info.  ([1, 2, 3])

    Note that it may be necessary to go back through all the deprecations
    before a release to make sure that the version number is correct.  So just
    use what you believe will be the next release number (this usually means
    bumping the minor number by one).

    To mark a function as deprecated, you can use the decorator
    @deprecated.

    See Also
    ========
    sympy.core.decorators.deprecated

    """

    def __init__(self, value=None, feature=None, last_supported_version=None,
                 useinstead=None, issue=None, deprecated_since_version=None):

        self.args = (value, feature, last_supported_version, useinstead,
                issue, deprecated_since_version)

        self.fullMessage = ""

        if not feature:
            raise ValueError("feature is required argument of SymPyDeprecationWarning")

        if not deprecated_since_version:
            raise ValueError("deprecated_since_version is a required argument of SymPyDeprecationWarning")

        self.fullMessage = "%s has been deprecated since SymPy %s. " % \
                                   (feature, deprecated_since_version)

        if last_supported_version:
            self.fullMessage += ("It will be last supported in SymPy "
                "version %s. ") % last_supported_version
        if useinstead:
            self.fullMessage += "Use %s instead. " % useinstead

        if not issue:
            raise ValueError("""\
The issue argument of SymPyDeprecationWarning is required.
This should be a separate issue with the "Deprecation Removal" label. See
https://github.com/sympy/sympy/wiki/Deprecating-policy.\
""")

        self.fullMessage += ("See "
            "https://github.com/sympy/sympy/issues/%d for more "
            "info. ") % issue

        if value:
            if not isinstance(value, string_types):
                value = "(%s)" % repr(value)
            value = " " + value
        else:
            value = ""

        self.fullMessage += value

    def __str__(self):
        return '\n%s\n' % filldedent(self.fullMessage)

    def warn(self, stacklevel=2):
        # the next line is what the user would see after the error is printed
        # if stacklevel was set to 1. If you are writing a wrapper around this,
        # increase the stacklevel accordingly.
        warnings.warn(self, stacklevel=stacklevel)

# Python by default hides DeprecationWarnings, which we do not want.
warnings.simplefilter("once", SymPyDeprecationWarning)
