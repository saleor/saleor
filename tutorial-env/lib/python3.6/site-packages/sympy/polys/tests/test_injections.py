"""Tests for functions that inject symbols into the global namespace. """

from sympy.polys.rings import vring
from sympy.polys.fields import vfield
from sympy.polys.domains import QQ
from sympy.utilities.pytest import raises

# make r1 with call-depth = 1

def _make_r1():
    return vring("r1", QQ)

# make r2 with call-depth = 2

def __make_r2():
    return vring("r2", QQ)

def _make_r2():
    return __make_r2()

def test_vring():
    R = vring("r", QQ)
    assert r == R.gens[0]

    R = vring("rb rbb rcc rzz _rx", QQ)
    assert rb == R.gens[0]
    assert rbb == R.gens[1]
    assert rcc == R.gens[2]
    assert rzz == R.gens[3]
    assert _rx == R.gens[4]

    R = vring(['rd', 're', 'rfg'], QQ)
    assert rd == R.gens[0]
    assert re == R.gens[1]
    assert rfg == R.gens[2]

    # see if vring() really injects into global namespace
    raises(NameError, lambda: r1)
    R = _make_r1()
    assert r1 == R.gens[0]

    raises(NameError, lambda: r2)
    R = _make_r2()
    assert r2 == R.gens[0]

# make f1 with call-depth = 1

def _make_f1():
    return vfield("f1", QQ)

# make f2 with call-depth = 2

def __make_f2():
    return vfield("f2", QQ)

def _make_f2():
    return __make_f2()

def test_vfield():
    F = vfield("f", QQ)
    assert f == F.gens[0]

    F = vfield("fb fbb fcc fzz _fx", QQ)
    assert fb == F.gens[0]
    assert fbb == F.gens[1]
    assert fcc == F.gens[2]
    assert fzz == F.gens[3]
    assert _fx == F.gens[4]

    F = vfield(['fd', 'fe', 'ffg'], QQ)
    assert fd == F.gens[0]
    assert fe == F.gens[1]
    assert ffg == F.gens[2]

    # see if vfield() really injects into global namespace
    raises(NameError, lambda: f1)
    F = _make_f1()
    assert f1 == F.gens[0]

    raises(NameError, lambda: f2)
    F = _make_f2()
    assert f2 == F.gens[0]
