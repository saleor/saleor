# -*- coding: utf-8 -*-
from __future__ import absolute_import

import shutil
from sympy.external import import_module
from sympy.utilities.pytest import skip

from sympy.utilities._compilation.compilation import compile_link_import_strings

numpy = import_module('numpy')
cython = import_module('cython')

_sources1 = [
    ('sigmoid.c', r"""
#include <math.h>

void sigmoid(int n, const double * const restrict in,
             double * const restrict out, double lim){
    for (int i=0; i<n; ++i){
        const double x = in[i];
        out[i] = x*pow(pow(x/lim, 8)+1, -1./8.);
    }
}
"""),
    ('_sigmoid.pyx', r"""
import numpy as np
cimport numpy as cnp

cdef extern void c_sigmoid "sigmoid" (int, const double * const,
                                      double * const, double)

def sigmoid(double [:] inp, double lim=350.0):
    cdef cnp.ndarray[cnp.float64_t, ndim=1] out = np.empty(
        inp.size, dtype=np.float64)
    c_sigmoid(inp.size, &inp[0], &out[0], lim)
    return out
""")
]


def npy(data, lim=350.0):
    return data/((data/lim)**8+1)**(1/8.)


def test_compile_link_import_strings():
    if not numpy:
        skip("numpy not installed.")
    if not cython:
        skip("cython not installed.")

    from sympy.utilities._compilation import has_c
    if not has_c():
        skip("No C compiler found.")

    compile_kw = dict(std='c99', include_dirs=[numpy.get_include()])
    info = None
    try:
        mod, info = compile_link_import_strings(_sources1, compile_kwargs=compile_kw)
        data = numpy.random.random(1024*1024*8)  # 64 MB of RAM needed..
        res_mod = mod.sigmoid(data)
        res_npy = npy(data)
        assert numpy.allclose(res_mod, res_npy)
    finally:
        if info and info['build_dir']:
            shutil.rmtree(info['build_dir'])
