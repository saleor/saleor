from pyxb.bundles.common.raw.xhtml1 import *
import pyxb.bundles.common.raw.xhtml1 as _raw

# The order of elements in an XHTML document is information that is
# not reflected in the schema information model.  For XHTML complex
# types replace the global validation configuration with one where the
# content list is strictly obeyed when generating documents.

DefaultValidationConfig = pyxb.GlobalValidationConfig.copy()
"""The validation configuration that applies to complex types in this namespace."""

DefaultValidationConfig._setContentInfluencesGeneration(DefaultValidationConfig.ALWAYS)
DefaultValidationConfig._setOrphanElementInContent(DefaultValidationConfig.RAISE_EXCEPTION)
DefaultValidationConfig._setInvalidElementInContent(DefaultValidationConfig.RAISE_EXCEPTION)

def _setValidationConfig ():
    import inspect
    import sys
    import pyxb.binding.basis

    for (n, v) in inspect.getmembers(_raw):
        if inspect.isclass(v) and issubclass(v, pyxb.binding.basis._TypeBinding_mixin):
            v._SetValidationConfig(DefaultValidationConfig)

_setValidationConfig()
