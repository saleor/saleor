__all__ = []

# The following pattern is used below for importing sub-modules:
#
# 1. "from foo import *".  This imports all the names from foo.__all__ into
#    this module. But, this does not put those names into the __all__ of
#    this module. This enables "from sympy.physics.optics import TWave" to
#    work.
# 2. "import foo; __all__.extend(foo.__all__)". This adds all the names in
#    foo.__all__ to the __all__ of this module. The names in __all__
#    determine which names are imported when
#    "from sympy.physics.optics import *" is done.

from . import waves
from .waves import TWave
__all__.extend(waves.__all__)


from . import gaussopt
from .gaussopt import (RayTransferMatrix, FreeSpace, FlatRefraction,
    CurvedRefraction, FlatMirror, CurvedMirror, ThinLens, GeometricRay,
    BeamParameter, waist2rayleigh, rayleigh2waist, geometric_conj_ab,
    geometric_conj_af, geometric_conj_bf, gaussian_conj, conjugate_gauss_beams)
__all__.extend(gaussopt.__all__)


from . import medium
from .medium import Medium
__all__.extend(medium.__all__)


from . import utils
from .utils import (refraction_angle, fresnel_coefficients,
        deviation, brewster_angle, critical_angle, lens_makers_formula,
    mirror_formula, lens_formula, hyperfocal_distance, transverse_magnification)
__all__.extend(utils.__all__)
