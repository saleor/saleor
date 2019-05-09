from sympy import S, pi, GoldenRatio as phi, sqrt
from sympy.ntheory.continued_fraction import \
    (continued_fraction_periodic as cf_p,
     continued_fraction_iterator as cf_i,
     continued_fraction_convergents as cf_c,
     continued_fraction_reduce as cf_r)
from sympy.utilities.pytest import raises


def test_continued_fraction():
    raises(ValueError, lambda: cf_p(1, 0, 0))
    raises(ValueError, lambda: cf_p(1, 1, -1))
    assert cf_p(4, 3, 0) == [1, 3]
    assert cf_p(0, 3, 5) == [0, 1, [2, 1, 12, 1, 2, 2]]
    assert cf_p(1, 1, 0) == [1]
    assert cf_p(3, 4, 0) == [0, 1, 3]
    assert cf_p(4, 5, 0) == [0, 1, 4]
    assert cf_p(5, 6, 0) == [0, 1, 5]
    assert cf_p(11, 13, 0) == [0, 1, 5, 2]
    assert cf_p(16, 19, 0) == [0, 1, 5, 3]
    assert cf_p(27, 32, 0) == [0, 1, 5, 2, 2]
    assert cf_p(1, 2, 5) == [[1]]
    assert cf_p(0, 1, 2) == [1, [2]]
    assert cf_p(6, 7, 49) == [1, 1, 6]
    assert cf_p(3796, 1387, 0) == [2, 1, 2, 1, 4]
    assert cf_p(3245, 10000) == [0, 3, 12, 4, 13]
    assert cf_p(1932, 2568) == [0, 1, 3, 26, 2]
    assert cf_p(6589, 2569) == [2, 1, 1, 3, 2, 1, 3, 1, 23]

    def take(iterator, n=7):
        res = []
        for i, t in enumerate(cf_i(iterator)):
            if i >= n:
                break
            res.append(t)
        return res

    assert take(phi) == [1, 1, 1, 1, 1, 1, 1]
    assert take(pi) == [3, 7, 15, 1, 292, 1, 1]

    assert list(cf_i(S(17)/12)) == [1, 2, 2, 2]
    assert list(cf_i(S(-17)/12)) == [-2, 1, 1, 2, 2]

    assert list(cf_c([1, 6, 1, 8])) == [S(1), S(7)/6, S(8)/7, S(71)/62]
    assert list(cf_c([2])) == [S(2)]
    assert list(cf_c([1, 1, 1, 1, 1, 1, 1])) == [S.One, S(2), S(3)/2, S(5)/3,
                                                 S(8)/5, S(13)/8, S(21)/13]
    assert list(cf_c([1, 6, S(-1)/2, 4])) == [S.One, S(7)/6, S(5)/4, S(3)/2]

    assert cf_r([1, 6, 1, 8]) == S(71)/62
    assert cf_r([3]) == S(3)
    assert cf_r([-1, 5, 1, 4]) == S(-24)/29
    assert (cf_r([0, 1, 1, 7, [24, 8]]) - (sqrt(3) + 2)/7).expand() == 0
    assert cf_r([1, 5, 9]) == S(55)/46
    assert (cf_r([[1]]) - (sqrt(5) + 1)/2).expand() == 0
