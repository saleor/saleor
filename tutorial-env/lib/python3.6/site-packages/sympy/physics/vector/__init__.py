__all__ = []

# The following pattern is used below for importing sub-modules:
#
# 1. "from foo import *".  This imports all the names from foo.__all__ into
#    this module. But, this does not put those names into the __all__ of
#    this module. This enables "from sympy.physics.vector import ReferenceFrame" to
#    work.
# 2. "import foo; __all__.extend(foo.__all__)". This adds all the names in
#    foo.__all__ to the __all__ of this module. The names in __all__
#    determine which names are imported when
#    "from sympy.physics.vector import *" is done.

from . import frame
from .frame import *
__all__.extend(frame.__all__)

from . import dyadic
from .dyadic import *
__all__.extend(dyadic.__all__)

from . import vector
from .vector import *
__all__.extend(vector.__all__)

from . import point
from .point import *
__all__.extend(point.__all__)

from . import functions
from .functions import *
__all__.extend(functions.__all__)

from . import printing
from .printing import *
__all__.extend(printing.__all__)

from . import fieldfunctions
from .fieldfunctions import *
__all__.extend(fieldfunctions.__all__)
