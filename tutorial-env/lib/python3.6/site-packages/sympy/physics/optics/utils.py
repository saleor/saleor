"""
**Contains**

* refraction_angle
* fresnel_coefficients
* deviation
* brewster_angle
* critical_angle
* lens_makers_formula
* mirror_formula
* lens_formula
* hyperfocal_distance
* transverse_magnification
"""

from __future__ import division

__all__ = ['refraction_angle',
           'deviation',
           'fresnel_coefficients',
           'brewster_angle',
           'critical_angle',
           'lens_makers_formula',
           'mirror_formula',
           'lens_formula',
           'hyperfocal_distance',
           'transverse_magnification'
           ]

from sympy import Symbol, sympify, sqrt, Matrix, acos, oo, Limit, atan2, asin,\
cos, sin, tan, I, cancel
from sympy.core.compatibility import is_sequence
from sympy.geometry.line import Ray3D, Point3D
from sympy.geometry.util import intersection
from sympy.geometry.plane import Plane
from .medium import Medium


def refraction_angle(incident, medium1, medium2, normal=None, plane=None):
    """
    This function calculates transmitted vector after refraction at planar
    surface. `medium1` and `medium2` can be `Medium` or any sympifiable object.

    If `incident` is an object of `Ray3D`, `normal` also has to be an instance
    of `Ray3D` in order to get the output as a `Ray3D`. Please note that if
    plane of separation is not provided and normal is an instance of `Ray3D`,
    normal will be assumed to be intersecting incident ray at the plane of
    separation. This will not be the case when `normal` is a `Matrix` or
    any other sequence.
    If `incident` is an instance of `Ray3D` and `plane` has not been provided
    and `normal` is not `Ray3D`, output will be a `Matrix`.

    Parameters
    ==========

    incident : Matrix, Ray3D, or sequence
        Incident vector
    medium1 : sympy.physics.optics.medium.Medium or sympifiable
        Medium 1 or its refractive index
    medium2 : sympy.physics.optics.medium.Medium or sympifiable
        Medium 2 or its refractive index
    normal : Matrix, Ray3D, or sequence
        Normal vector
    plane : Plane
        Plane of separation of the two media.

    Examples
    ========

    >>> from sympy.physics.optics import refraction_angle
    >>> from sympy.geometry import Point3D, Ray3D, Plane
    >>> from sympy.matrices import Matrix
    >>> from sympy import symbols
    >>> n = Matrix([0, 0, 1])
    >>> P = Plane(Point3D(0, 0, 0), normal_vector=[0, 0, 1])
    >>> r1 = Ray3D(Point3D(-1, -1, 1), Point3D(0, 0, 0))
    >>> refraction_angle(r1, 1, 1, n)
    Matrix([
    [ 1],
    [ 1],
    [-1]])
    >>> refraction_angle(r1, 1, 1, plane=P)
    Ray3D(Point3D(0, 0, 0), Point3D(1, 1, -1))

    With different index of refraction of the two media

    >>> n1, n2 = symbols('n1, n2')
    >>> refraction_angle(r1, n1, n2, n)
    Matrix([
    [                                n1/n2],
    [                                n1/n2],
    [-sqrt(3)*sqrt(-2*n1**2/(3*n2**2) + 1)]])
    >>> refraction_angle(r1, n1, n2, plane=P)
    Ray3D(Point3D(0, 0, 0), Point3D(n1/n2, n1/n2, -sqrt(3)*sqrt(-2*n1**2/(3*n2**2) + 1)))

    """
    # A flag to check whether to return Ray3D or not
    return_ray = False

    if plane is not None and normal is not None:
        raise ValueError("Either plane or normal is acceptable.")

    if not isinstance(incident, Matrix):
        if is_sequence(incident):
            _incident = Matrix(incident)
        elif isinstance(incident, Ray3D):
            _incident = Matrix(incident.direction_ratio)
        else:
            raise TypeError(
                "incident should be a Matrix, Ray3D, or sequence")
    else:
        _incident = incident

    # If plane is provided, get direction ratios of the normal
    # to the plane from the plane else go with `normal` param.
    if plane is not None:
        if not isinstance(plane, Plane):
            raise TypeError("plane should be an instance of geometry.plane.Plane")
        # If we have the plane, we can get the intersection
        # point of incident ray and the plane and thus return
        # an instance of Ray3D.
        if isinstance(incident, Ray3D):
            return_ray = True
            intersection_pt = plane.intersection(incident)[0]
        _normal = Matrix(plane.normal_vector)
    else:
        if not isinstance(normal, Matrix):
            if is_sequence(normal):
                _normal = Matrix(normal)
            elif isinstance(normal, Ray3D):
                _normal = Matrix(normal.direction_ratio)
                if isinstance(incident, Ray3D):
                    intersection_pt = intersection(incident, normal)
                    if len(intersection_pt) == 0:
                        raise ValueError(
                            "Normal isn't concurrent with the incident ray.")
                    else:
                        return_ray = True
                        intersection_pt = intersection_pt[0]
            else:
                raise TypeError(
                    "Normal should be a Matrix, Ray3D, or sequence")
        else:
            _normal = normal

    n1, n2 = None, None

    if isinstance(medium1, Medium):
        n1 = medium1.refractive_index
    else:
        n1 = sympify(medium1)

    if isinstance(medium2, Medium):
        n2 = medium2.refractive_index
    else:
        n2 = sympify(medium2)

    eta = n1/n2  # Relative index of refraction
    # Calculating magnitude of the vectors
    mag_incident = sqrt(sum([i**2 for i in _incident]))
    mag_normal = sqrt(sum([i**2 for i in _normal]))
    # Converting vectors to unit vectors by dividing
    # them with their magnitudes
    _incident /= mag_incident
    _normal /= mag_normal
    c1 = -_incident.dot(_normal)  # cos(angle_of_incidence)
    cs2 = 1 - eta**2*(1 - c1**2)  # cos(angle_of_refraction)**2
    if cs2.is_negative:  # This is the case of total internal reflection(TIR).
        return 0
    drs = eta*_incident + (eta*c1 - sqrt(cs2))*_normal
    # Multiplying unit vector by its magnitude
    drs = drs*mag_incident
    if not return_ray:
        return drs
    else:
        return Ray3D(intersection_pt, direction_ratio=drs)


def fresnel_coefficients(angle_of_incidence, medium1, medium2):
    """
    This function uses Fresnel equations to calculate reflection and
    transmission coefficients. Those are obtained for both polarisations
    when the electric field vector is in the plane of incidence (labelled 'p')
    and when the electric field vector is perpendicular to the plane of
    incidence (labelled 's'). There are four real coefficients unless the
    incident ray reflects in total internal in which case there are two complex
    ones. Angle of incidence is the angle between the incident ray and the
    surface normal. ``medium1`` and ``medium2`` can be ``Medium`` or any
    sympifiable object.

    Parameters
    ==========

    angle_of_incidence : sympifiable

    medium1 : Medium or sympifiable
        Medium 1 or its refractive index

    medium2 : Medium or sympifiable
        Medium 2 or its refractive index

    Returns a list with four real Fresnel coefficients:
    [reflection p (TM), reflection s (TE),
    transmission p (TM), transmission s (TE)]
    If the ray is undergoes total internal reflection then returns a
    list of two complex Fresnel coefficients:
    [reflection p (TM), reflection s (TE)]

    Examples
    ========

    >>> from sympy.physics.optics import fresnel_coefficients
    >>> fresnel_coefficients(0.3, 1, 2)
    [0.317843553417859, -0.348645229818821,
            0.658921776708929, 0.651354770181179]
    >>> fresnel_coefficients(0.6, 2, 1)
    [-0.235625382192159 - 0.971843958291041*I,
             0.816477005968898 - 0.577377951366403*I]

    References
    ==========

    https://en.wikipedia.org/wiki/Fresnel_equations
    """

    if isinstance(medium1, Medium):
        n1 = medium1.refractive_index
    else:
        n1 = sympify(medium1)

    if isinstance(medium2, Medium):
        n2 = medium2.refractive_index
    else:
        n2 = sympify(medium2)

    angle_of_refraction = asin(n1*sin(angle_of_incidence)/n2)
    try:
        angle_of_total_internal_reflection_onset = critical_angle(n1, n2)
    except ValueError:
        angle_of_total_internal_reflection_onset = None

    if angle_of_total_internal_reflection_onset == None or\
    angle_of_total_internal_reflection_onset > angle_of_incidence:
        R_s = -sin(angle_of_incidence - angle_of_refraction)\
                /sin(angle_of_incidence + angle_of_refraction)
        R_p = tan(angle_of_incidence - angle_of_refraction)\
                /tan(angle_of_incidence + angle_of_refraction)
        T_s = 2*sin(angle_of_refraction)*cos(angle_of_incidence)\
                /sin(angle_of_incidence + angle_of_refraction)
        T_p = 2*sin(angle_of_refraction)*cos(angle_of_incidence)\
                /(sin(angle_of_incidence + angle_of_refraction)\
                *cos(angle_of_incidence - angle_of_refraction))
        return [R_p, R_s, T_p, T_s]
    else:
        n = n2/n1
        R_s = cancel((cos(angle_of_incidence)-\
                I*sqrt(sin(angle_of_incidence)**2 - n**2))\
                /(cos(angle_of_incidence)+\
                I*sqrt(sin(angle_of_incidence)**2 - n**2)))
        R_p = cancel((n**2*cos(angle_of_incidence)-\
                I*sqrt(sin(angle_of_incidence)**2 - n**2))\
                /(n**2*cos(angle_of_incidence)+\
                I*sqrt(sin(angle_of_incidence)**2 - n**2)))
        return [R_p, R_s]


def deviation(incident, medium1, medium2, normal=None, plane=None):
    """
    This function calculates the angle of deviation of a ray
    due to refraction at planar surface.

    Parameters
    ==========

    incident : Matrix, Ray3D, or sequence
        Incident vector
    medium1 : sympy.physics.optics.medium.Medium or sympifiable
        Medium 1 or its refractive index
    medium2 : sympy.physics.optics.medium.Medium or sympifiable
        Medium 2 or its refractive index
    normal : Matrix, Ray3D, or sequence
        Normal vector
    plane : Plane
        Plane of separation of the two media.

    Examples
    ========

    >>> from sympy.physics.optics import deviation
    >>> from sympy.geometry import Point3D, Ray3D, Plane
    >>> from sympy.matrices import Matrix
    >>> from sympy import symbols
    >>> n1, n2 = symbols('n1, n2')
    >>> n = Matrix([0, 0, 1])
    >>> P = Plane(Point3D(0, 0, 0), normal_vector=[0, 0, 1])
    >>> r1 = Ray3D(Point3D(-1, -1, 1), Point3D(0, 0, 0))
    >>> deviation(r1, 1, 1, n)
    0
    >>> deviation(r1, n1, n2, plane=P)
    -acos(-sqrt(-2*n1**2/(3*n2**2) + 1)) + acos(-sqrt(3)/3)

    """
    refracted = refraction_angle(incident,
                                 medium1,
                                 medium2,
                                 normal=normal,
                                 plane=plane)
    if refracted != 0:
        if isinstance(refracted, Ray3D):
            refracted = Matrix(refracted.direction_ratio)

        if not isinstance(incident, Matrix):
            if is_sequence(incident):
                _incident = Matrix(incident)
            elif isinstance(incident, Ray3D):
                _incident = Matrix(incident.direction_ratio)
            else:
                raise TypeError(
                    "incident should be a Matrix, Ray3D, or sequence")
        else:
            _incident = incident

        if plane is None:
            if not isinstance(normal, Matrix):
                if is_sequence(normal):
                    _normal = Matrix(normal)
                elif isinstance(normal, Ray3D):
                    _normal = Matrix(normal.direction_ratio)
                else:
                    raise TypeError(
                        "normal should be a Matrix, Ray3D, or sequence")
            else:
                _normal = normal
        else:
            _normal = Matrix(plane.normal_vector)

        mag_incident = sqrt(sum([i**2 for i in _incident]))
        mag_normal = sqrt(sum([i**2 for i in _normal]))
        mag_refracted = sqrt(sum([i**2 for i in refracted]))
        _incident /= mag_incident
        _normal /= mag_normal
        refracted /= mag_refracted
        i = acos(_incident.dot(_normal))
        r = acos(refracted.dot(_normal))
        return i - r


def brewster_angle(medium1, medium2):
    """
    This function calculates the Brewster's angle of incidence to Medium 2 from
    Medium 1 in radians.

    Parameters
    ==========

    medium 1 : Medium or sympifiable
        Refractive index of Medium 1
    medium 2 : Medium or sympifiable
        Refractive index of Medium 1

    Examples
    ========

    >>> from sympy.physics.optics import brewster_angle
    >>> brewster_angle(1, 1.33)
    0.926093295503462

    """
    n1, n2 = None, None

    if isinstance(medium1, Medium):
        n1 = medium1.refractive_index
    else:
        n1 = sympify(medium1)

    if isinstance(medium2, Medium):
        n2 = medium2.refractive_index
    else:
        n2 = sympify(medium2)

    return atan2(n2, n1)

def critical_angle(medium1, medium2):
    """
    This function calculates the critical angle of incidence (marking the onset
    of total internal) to Medium 2 from Medium 1 in radians.

    Parameters
    ==========

    medium 1 : Medium or sympifiable
        Refractive index of Medium 1
    medium 2 : Medium or sympifiable
        Refractive index of Medium 1

    Examples
    ========

    >>> from sympy.physics.optics import critical_angle
    >>> critical_angle(1.33, 1)
    0.850908514477849

    """
    n1, n2 = None, None

    if isinstance(medium1, Medium):
        n1 = medium1.refractive_index
    else:
        n1 = sympify(medium1)

    if isinstance(medium2, Medium):
        n2 = medium2.refractive_index
    else:
        n2 = sympify(medium2)

    if n2 > n1:
        raise ValueError('Total internal reflection impossible for n1 < n2')
    else:
        return asin(n2/n1)



def lens_makers_formula(n_lens, n_surr, r1, r2):
    """
    This function calculates focal length of a thin lens.
    It follows cartesian sign convention.

    Parameters
    ==========

    n_lens : Medium or sympifiable
        Index of refraction of lens.
    n_surr : Medium or sympifiable
        Index of reflection of surrounding.
    r1 : sympifiable
        Radius of curvature of first surface.
    r2 : sympifiable
        Radius of curvature of second surface.

    Examples
    ========

    >>> from sympy.physics.optics import lens_makers_formula
    >>> lens_makers_formula(1.33, 1, 10, -10)
    15.1515151515151

    """
    if isinstance(n_lens, Medium):
        n_lens = n_lens.refractive_index
    else:
        n_lens = sympify(n_lens)
    if isinstance(n_surr, Medium):
        n_surr = n_surr.refractive_index
    else:
        n_surr = sympify(n_surr)

    r1 = sympify(r1)
    r2 = sympify(r2)

    return 1/((n_lens - n_surr)/n_surr*(1/r1 - 1/r2))


def mirror_formula(focal_length=None, u=None, v=None):
    """
    This function provides one of the three parameters
    when two of them are supplied.
    This is valid only for paraxial rays.

    Parameters
    ==========

    focal_length : sympifiable
        Focal length of the mirror.
    u : sympifiable
        Distance of object from the pole on
        the principal axis.
    v : sympifiable
        Distance of the image from the pole
        on the principal axis.

    Examples
    ========

    >>> from sympy.physics.optics import mirror_formula
    >>> from sympy.abc import f, u, v
    >>> mirror_formula(focal_length=f, u=u)
    f*u/(-f + u)
    >>> mirror_formula(focal_length=f, v=v)
    f*v/(-f + v)
    >>> mirror_formula(u=u, v=v)
    u*v/(u + v)

    """
    if focal_length and u and v:
        raise ValueError("Please provide only two parameters")

    focal_length = sympify(focal_length)
    u = sympify(u)
    v = sympify(v)
    if u == oo:
        _u = Symbol('u')
    if v == oo:
        _v = Symbol('v')
    if focal_length == oo:
        _f = Symbol('f')
    if focal_length is None:
        if u == oo and v == oo:
            return Limit(Limit(_v*_u/(_v + _u), _u, oo), _v, oo).doit()
        if u == oo:
            return Limit(v*_u/(v + _u), _u, oo).doit()
        if v == oo:
            return Limit(_v*u/(_v + u), _v, oo).doit()
        return v*u/(v + u)
    if u is None:
        if v == oo and focal_length == oo:
            return Limit(Limit(_v*_f/(_v - _f), _v, oo), _f, oo).doit()
        if v == oo:
            return Limit(_v*focal_length/(_v - focal_length), _v, oo).doit()
        if focal_length == oo:
            return Limit(v*_f/(v - _f), _f, oo).doit()
        return v*focal_length/(v - focal_length)
    if v is None:
        if u == oo and focal_length == oo:
            return Limit(Limit(_u*_f/(_u - _f), _u, oo), _f, oo).doit()
        if u == oo:
            return Limit(_u*focal_length/(_u - focal_length), _u, oo).doit()
        if focal_length == oo:
            return Limit(u*_f/(u - _f), _f, oo).doit()
        return u*focal_length/(u - focal_length)


def lens_formula(focal_length=None, u=None, v=None):
    """
    This function provides one of the three parameters
    when two of them are supplied.
    This is valid only for paraxial rays.

    Parameters
    ==========

    focal_length : sympifiable
        Focal length of the mirror.
    u : sympifiable
        Distance of object from the optical center on
        the principal axis.
    v : sympifiable
        Distance of the image from the optical center
        on the principal axis.

    Examples
    ========

    >>> from sympy.physics.optics import lens_formula
    >>> from sympy.abc import f, u, v
    >>> lens_formula(focal_length=f, u=u)
    f*u/(f + u)
    >>> lens_formula(focal_length=f, v=v)
    f*v/(f - v)
    >>> lens_formula(u=u, v=v)
    u*v/(u - v)

    """
    if focal_length and u and v:
        raise ValueError("Please provide only two parameters")

    focal_length = sympify(focal_length)
    u = sympify(u)
    v = sympify(v)
    if u == oo:
        _u = Symbol('u')
    if v == oo:
        _v = Symbol('v')
    if focal_length == oo:
        _f = Symbol('f')
    if focal_length is None:
        if u == oo and v == oo:
            return Limit(Limit(_v*_u/(_u - _v), _u, oo), _v, oo).doit()
        if u == oo:
            return Limit(v*_u/(_u - v), _u, oo).doit()
        if v == oo:
            return Limit(_v*u/(u - _v), _v, oo).doit()
        return v*u/(u - v)
    if u is None:
        if v == oo and focal_length == oo:
            return Limit(Limit(_v*_f/(_f - _v), _v, oo), _f, oo).doit()
        if v == oo:
            return Limit(_v*focal_length/(focal_length - _v), _v, oo).doit()
        if focal_length == oo:
            return Limit(v*_f/(_f - v), _f, oo).doit()
        return v*focal_length/(focal_length - v)
    if v is None:
        if u == oo and focal_length == oo:
            return Limit(Limit(_u*_f/(_u + _f), _u, oo), _f, oo).doit()
        if u == oo:
            return Limit(_u*focal_length/(_u + focal_length), _u, oo).doit()
        if focal_length == oo:
            return Limit(u*_f/(u + _f), _f, oo).doit()
        return u*focal_length/(u + focal_length)

def hyperfocal_distance(f, N, c):
    """

    Parameters
    ==========
    f: sympifiable
    Focal length of a given lens

    N: sympifiable
    F-number of a given lens

    c: sympifiable
    Circle of Confusion (CoC) of a given image format

    Example
    =======
    >>> from sympy.physics.optics import hyperfocal_distance
    >>> from sympy.abc import f, N, c
    >>> round(hyperfocal_distance(f = 0.5, N = 8, c = 0.0033), 2)
    9.47
    """

    f = sympify(f)
    N = sympify(N)
    c = sympify(c)

    return (1/(N * c))*(f**2)

def transverse_magnification(si, so):
    """

    Calculates the transverse magnification, which is the ratio of the
    image size to the object size.

    Parameters
    ==========
    so: sympifiable
    Lens-object distance

    si: sympifiable
    Lens-image distance

    Example
    =======
    >>> from sympy.physics.optics import transverse_magnification
    >>> transverse_magnification(30, 15)
    -2

    """

    si = sympify(si)
    so = sympify(so)

    return (-(si/so))
