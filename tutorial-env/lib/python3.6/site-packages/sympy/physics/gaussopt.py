from sympy.physics.optics.gaussopt import RayTransferMatrix, FreeSpace,\
    FlatRefraction, CurvedRefraction, FlatMirror, CurvedMirror, ThinLens,\
    GeometricRay, BeamParameter, waist2rayleigh, rayleigh2waist, geometric_conj_ab,\
    geometric_conj_af, geometric_conj_bf, gaussian_conj, conjugate_gauss_beams

from sympy.utilities.exceptions import SymPyDeprecationWarning


SymPyDeprecationWarning(feature="Module sympy.physics.gaussopt",
        useinstead="sympy.physics.optics.gaussopt",
        deprecated_since_version="0.7.6", issue=7659).warn()
