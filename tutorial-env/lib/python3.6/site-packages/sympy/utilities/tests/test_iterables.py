from __future__ import print_function
from textwrap import dedent

from sympy import (
    symbols, Integral, Tuple, Dummy, Basic, default_sort_key, Matrix,
    factorial, true)
from sympy.combinatorics import RGS_enum, RGS_unrank, Permutation
from sympy.core.compatibility import range
from sympy.utilities.iterables import (
    _partition, _set_partitions, binary_partitions, bracelets, capture,
    cartes, common_prefix, common_suffix, connected_components, dict_merge,
    filter_symbols, flatten, generate_bell, generate_derangements,
    generate_involutions, generate_oriented_forest, group, has_dups, ibin,
    kbins, minlex, multiset, multiset_combinations, multiset_partitions,
    multiset_permutations, necklaces, numbered_symbols, ordered, partitions,
    permutations, postfixes, postorder_traversal, prefixes, reshape,
    rotate_left, rotate_right, runs, sift, strongly_connected_components,
    subsets, take, topological_sort, unflatten, uniq, variations,
    ordered_partitions, rotations)
from sympy.utilities.enumerative import (
    factoring_visitor, multiset_partitions_taocp )

from sympy.core.singleton import S
from sympy.functions.elementary.piecewise import Piecewise, ExprCondPair
from sympy.utilities.pytest import raises

w, x, y, z = symbols('w,x,y,z')


def test_postorder_traversal():
    expr = z + w*(x + y)
    expected = [z, w, x, y, x + y, w*(x + y), w*(x + y) + z]
    assert list(postorder_traversal(expr, keys=default_sort_key)) == expected
    assert list(postorder_traversal(expr, keys=True)) == expected

    expr = Piecewise((x, x < 1), (x**2, True))
    expected = [
        x, 1, x, x < 1, ExprCondPair(x, x < 1),
        2, x, x**2, true,
        ExprCondPair(x**2, True), Piecewise((x, x < 1), (x**2, True))
    ]
    assert list(postorder_traversal(expr, keys=default_sort_key)) == expected
    assert list(postorder_traversal(
        [expr], keys=default_sort_key)) == expected + [[expr]]

    assert list(postorder_traversal(Integral(x**2, (x, 0, 1)),
        keys=default_sort_key)) == [
            2, x, x**2, 0, 1, x, Tuple(x, 0, 1),
            Integral(x**2, Tuple(x, 0, 1))
        ]
    assert list(postorder_traversal(('abc', ('d', 'ef')))) == [
        'abc', 'd', 'ef', ('d', 'ef'), ('abc', ('d', 'ef'))]


def test_flatten():
    assert flatten((1, (1,))) == [1, 1]
    assert flatten((x, (x,))) == [x, x]

    ls = [[(-2, -1), (1, 2)], [(0, 0)]]

    assert flatten(ls, levels=0) == ls
    assert flatten(ls, levels=1) == [(-2, -1), (1, 2), (0, 0)]
    assert flatten(ls, levels=2) == [-2, -1, 1, 2, 0, 0]
    assert flatten(ls, levels=3) == [-2, -1, 1, 2, 0, 0]

    raises(ValueError, lambda: flatten(ls, levels=-1))

    class MyOp(Basic):
        pass

    assert flatten([MyOp(x, y), z]) == [MyOp(x, y), z]
    assert flatten([MyOp(x, y), z], cls=MyOp) == [x, y, z]

    assert flatten({1, 11, 2}) == list({1, 11, 2})


def test_group():
    assert group([]) == []
    assert group([], multiple=False) == []

    assert group([1]) == [[1]]
    assert group([1], multiple=False) == [(1, 1)]

    assert group([1, 1]) == [[1, 1]]
    assert group([1, 1], multiple=False) == [(1, 2)]

    assert group([1, 1, 1]) == [[1, 1, 1]]
    assert group([1, 1, 1], multiple=False) == [(1, 3)]

    assert group([1, 2, 1]) == [[1], [2], [1]]
    assert group([1, 2, 1], multiple=False) == [(1, 1), (2, 1), (1, 1)]

    assert group([1, 1, 2, 2, 2, 1, 3, 3]) == [[1, 1], [2, 2, 2], [1], [3, 3]]
    assert group([1, 1, 2, 2, 2, 1, 3, 3], multiple=False) == [(1, 2),
                 (2, 3), (1, 1), (3, 2)]


def test_subsets():
    # combinations
    assert list(subsets([1, 2, 3], 0)) == [()]
    assert list(subsets([1, 2, 3], 1)) == [(1,), (2,), (3,)]
    assert list(subsets([1, 2, 3], 2)) == [(1, 2), (1, 3), (2, 3)]
    assert list(subsets([1, 2, 3], 3)) == [(1, 2, 3)]
    l = list(range(4))
    assert list(subsets(l, 0, repetition=True)) == [()]
    assert list(subsets(l, 1, repetition=True)) == [(0,), (1,), (2,), (3,)]
    assert list(subsets(l, 2, repetition=True)) == [(0, 0), (0, 1), (0, 2),
                                                    (0, 3), (1, 1), (1, 2),
                                                    (1, 3), (2, 2), (2, 3),
                                                    (3, 3)]
    assert list(subsets(l, 3, repetition=True)) == [(0, 0, 0), (0, 0, 1),
                                                    (0, 0, 2), (0, 0, 3),
                                                    (0, 1, 1), (0, 1, 2),
                                                    (0, 1, 3), (0, 2, 2),
                                                    (0, 2, 3), (0, 3, 3),
                                                    (1, 1, 1), (1, 1, 2),
                                                    (1, 1, 3), (1, 2, 2),
                                                    (1, 2, 3), (1, 3, 3),
                                                    (2, 2, 2), (2, 2, 3),
                                                    (2, 3, 3), (3, 3, 3)]
    assert len(list(subsets(l, 4, repetition=True))) == 35

    assert list(subsets(l[:2], 3, repetition=False)) == []
    assert list(subsets(l[:2], 3, repetition=True)) == [(0, 0, 0),
                                                        (0, 0, 1),
                                                        (0, 1, 1),
                                                        (1, 1, 1)]
    assert list(subsets([1, 2], repetition=True)) == \
        [(), (1,), (2,), (1, 1), (1, 2), (2, 2)]
    assert list(subsets([1, 2], repetition=False)) == \
        [(), (1,), (2,), (1, 2)]
    assert list(subsets([1, 2, 3], 2)) == \
        [(1, 2), (1, 3), (2, 3)]
    assert list(subsets([1, 2, 3], 2, repetition=True)) == \
        [(1, 1), (1, 2), (1, 3), (2, 2), (2, 3), (3, 3)]


def test_variations():
    # permutations
    l = list(range(4))
    assert list(variations(l, 0, repetition=False)) == [()]
    assert list(variations(l, 1, repetition=False)) == [(0,), (1,), (2,), (3,)]
    assert list(variations(l, 2, repetition=False)) == [(0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (1, 3), (2, 0), (2, 1), (2, 3), (3, 0), (3, 1), (3, 2)]
    assert list(variations(l, 3, repetition=False)) == [(0, 1, 2), (0, 1, 3), (0, 2, 1), (0, 2, 3), (0, 3, 1), (0, 3, 2), (1, 0, 2), (1, 0, 3), (1, 2, 0), (1, 2, 3), (1, 3, 0), (1, 3, 2), (2, 0, 1), (2, 0, 3), (2, 1, 0), (2, 1, 3), (2, 3, 0), (2, 3, 1), (3, 0, 1), (3, 0, 2), (3, 1, 0), (3, 1, 2), (3, 2, 0), (3, 2, 1)]
    assert list(variations(l, 0, repetition=True)) == [()]
    assert list(variations(l, 1, repetition=True)) == [(0,), (1,), (2,), (3,)]
    assert list(variations(l, 2, repetition=True)) == [(0, 0), (0, 1), (0, 2),
                                                       (0, 3), (1, 0), (1, 1),
                                                       (1, 2), (1, 3), (2, 0),
                                                       (2, 1), (2, 2), (2, 3),
                                                       (3, 0), (3, 1), (3, 2),
                                                       (3, 3)]
    assert len(list(variations(l, 3, repetition=True))) == 64
    assert len(list(variations(l, 4, repetition=True))) == 256
    assert list(variations(l[:2], 3, repetition=False)) == []
    assert list(variations(l[:2], 3, repetition=True)) == [
        (0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1),
        (1, 0, 0), (1, 0, 1), (1, 1, 0), (1, 1, 1)
    ]


def test_cartes():
    assert list(cartes([1, 2], [3, 4, 5])) == \
        [(1, 3), (1, 4), (1, 5), (2, 3), (2, 4), (2, 5)]
    assert list(cartes()) == [()]
    assert list(cartes('a')) == [('a',)]
    assert list(cartes('a', repeat=2)) == [('a', 'a')]
    assert list(cartes(list(range(2)))) == [(0,), (1,)]

def test_filter_symbols():
    s = numbered_symbols()
    filtered = filter_symbols(s, symbols("x0 x2 x3"))
    assert take(filtered, 3) == list(symbols("x1 x4 x5"))

def test_numbered_symbols():
    s = numbered_symbols(cls=Dummy)
    assert isinstance(next(s), Dummy)
    assert next(numbered_symbols('C', start=1, exclude=[symbols('C1')])) == \
        symbols('C2')


def test_sift():
    assert sift(list(range(5)), lambda _: _ % 2) == {1: [1, 3], 0: [0, 2, 4]}
    assert sift([x, y], lambda _: _.has(x)) == {False: [y], True: [x]}
    assert sift([S.One], lambda _: _.has(x)) == {False: [1]}
    assert sift([0, 1, 2, 3], lambda x: x % 2, binary=True) == (
        [1, 3], [0, 2])
    assert sift([0, 1, 2, 3], lambda x: x % 3 == 1, binary=True) == (
        [1], [0, 2, 3])
    raises(ValueError, lambda:
        sift([0, 1, 2, 3], lambda x: x % 3, binary=True))


def test_take():
    X = numbered_symbols()

    assert take(X, 5) == list(symbols('x0:5'))
    assert take(X, 5) == list(symbols('x5:10'))

    assert take([1, 2, 3, 4, 5], 5) == [1, 2, 3, 4, 5]


def test_dict_merge():
    assert dict_merge({}, {1: x, y: z}) == {1: x, y: z}
    assert dict_merge({1: x, y: z}, {}) == {1: x, y: z}

    assert dict_merge({2: z}, {1: x, y: z}) == {1: x, 2: z, y: z}
    assert dict_merge({1: x, y: z}, {2: z}) == {1: x, 2: z, y: z}

    assert dict_merge({1: y, 2: z}, {1: x, y: z}) == {1: x, 2: z, y: z}
    assert dict_merge({1: x, y: z}, {1: y, 2: z}) == {1: y, 2: z, y: z}


def test_prefixes():
    assert list(prefixes([])) == []
    assert list(prefixes([1])) == [[1]]
    assert list(prefixes([1, 2])) == [[1], [1, 2]]

    assert list(prefixes([1, 2, 3, 4, 5])) == \
        [[1], [1, 2], [1, 2, 3], [1, 2, 3, 4], [1, 2, 3, 4, 5]]


def test_postfixes():
    assert list(postfixes([])) == []
    assert list(postfixes([1])) == [[1]]
    assert list(postfixes([1, 2])) == [[2], [1, 2]]

    assert list(postfixes([1, 2, 3, 4, 5])) == \
        [[5], [4, 5], [3, 4, 5], [2, 3, 4, 5], [1, 2, 3, 4, 5]]


def test_topological_sort():
    V = [2, 3, 5, 7, 8, 9, 10, 11]
    E = [(7, 11), (7, 8), (5, 11),
         (3, 8), (3, 10), (11, 2),
         (11, 9), (11, 10), (8, 9)]

    assert topological_sort((V, E)) == [3, 5, 7, 8, 11, 2, 9, 10]
    assert topological_sort((V, E), key=lambda v: -v) == \
        [7, 5, 11, 3, 10, 8, 9, 2]

    raises(ValueError, lambda: topological_sort((V, E + [(10, 7)])))


def test_strongly_connected_components():
    assert strongly_connected_components(([], [])) == []
    assert strongly_connected_components(([1, 2, 3], [])) == [[1], [2], [3]]

    V = [1, 2, 3]
    E = [(1, 2), (1, 3), (2, 1), (2, 3), (3, 1)]
    assert strongly_connected_components((V, E)) == [[1, 2, 3]]

    V = [1, 2, 3, 4]
    E = [(1, 2), (2, 3), (3, 2), (3, 4)]
    assert strongly_connected_components((V, E)) == [[4], [2, 3], [1]]

    V = [1, 2, 3, 4]
    E = [(1, 2), (2, 1), (3, 4), (4, 3)]
    assert strongly_connected_components((V, E)) == [[1, 2], [3, 4]]


def test_connected_components():
    assert connected_components(([], [])) == []
    assert connected_components(([1, 2, 3], [])) == [[1], [2], [3]]

    V = [1, 2, 3]
    E = [(1, 2), (1, 3), (2, 1), (2, 3), (3, 1)]
    assert connected_components((V, E)) == [[1, 2, 3]]

    V = [1, 2, 3, 4]
    E = [(1, 2), (2, 3), (3, 2), (3, 4)]
    assert connected_components((V, E)) == [[1, 2, 3, 4]]

    V = [1, 2, 3, 4]
    E = [(1, 2), (3, 4)]
    assert connected_components((V, E)) == [[1, 2], [3, 4]]


def test_rotate():
    A = [0, 1, 2, 3, 4]

    assert rotate_left(A, 2) == [2, 3, 4, 0, 1]
    assert rotate_right(A, 1) == [4, 0, 1, 2, 3]
    A = []
    B = rotate_right(A, 1)
    assert B == []
    B.append(1)
    assert A == []
    B = rotate_left(A, 1)
    assert B == []
    B.append(1)
    assert A == []


def test_multiset_partitions():
    A = [0, 1, 2, 3, 4]

    assert list(multiset_partitions(A, 5)) == [[[0], [1], [2], [3], [4]]]
    assert len(list(multiset_partitions(A, 4))) == 10
    assert len(list(multiset_partitions(A, 3))) == 25

    assert list(multiset_partitions([1, 1, 1, 2, 2], 2)) == [
        [[1, 1, 1, 2], [2]], [[1, 1, 1], [2, 2]], [[1, 1, 2, 2], [1]],
        [[1, 1, 2], [1, 2]], [[1, 1], [1, 2, 2]]]

    assert list(multiset_partitions([1, 1, 2, 2], 2)) == [
        [[1, 1, 2], [2]], [[1, 1], [2, 2]], [[1, 2, 2], [1]],
        [[1, 2], [1, 2]]]

    assert list(multiset_partitions([1, 2, 3, 4], 2)) == [
        [[1, 2, 3], [4]], [[1, 2, 4], [3]], [[1, 2], [3, 4]],
        [[1, 3, 4], [2]], [[1, 3], [2, 4]], [[1, 4], [2, 3]],
        [[1], [2, 3, 4]]]

    assert list(multiset_partitions([1, 2, 2], 2)) == [
        [[1, 2], [2]], [[1], [2, 2]]]

    assert list(multiset_partitions(3)) == [
        [[0, 1, 2]], [[0, 1], [2]], [[0, 2], [1]], [[0], [1, 2]],
        [[0], [1], [2]]]
    assert list(multiset_partitions(3, 2)) == [
        [[0, 1], [2]], [[0, 2], [1]], [[0], [1, 2]]]
    assert list(multiset_partitions([1] * 3, 2)) == [[[1], [1, 1]]]
    assert list(multiset_partitions([1] * 3)) == [
        [[1, 1, 1]], [[1], [1, 1]], [[1], [1], [1]]]
    a = [3, 2, 1]
    assert list(multiset_partitions(a)) == \
        list(multiset_partitions(sorted(a)))
    assert list(multiset_partitions(a, 5)) == []
    assert list(multiset_partitions(a, 1)) == [[[1, 2, 3]]]
    assert list(multiset_partitions(a + [4], 5)) == []
    assert list(multiset_partitions(a + [4], 1)) == [[[1, 2, 3, 4]]]
    assert list(multiset_partitions(2, 5)) == []
    assert list(multiset_partitions(2, 1)) == [[[0, 1]]]
    assert list(multiset_partitions('a')) == [[['a']]]
    assert list(multiset_partitions('a', 2)) == []
    assert list(multiset_partitions('ab')) == [[['a', 'b']], [['a'], ['b']]]
    assert list(multiset_partitions('ab', 1)) == [[['a', 'b']]]
    assert list(multiset_partitions('aaa', 1)) == [['aaa']]
    assert list(multiset_partitions([1, 1], 1)) == [[[1, 1]]]
    ans = [('mpsyy',), ('mpsy', 'y'), ('mps', 'yy'), ('mps', 'y', 'y'),
           ('mpyy', 's'), ('mpy', 'sy'), ('mpy', 's', 'y'), ('mp', 'syy'),
           ('mp', 'sy', 'y'), ('mp', 's', 'yy'), ('mp', 's', 'y', 'y'),
           ('msyy', 'p'), ('msy', 'py'), ('msy', 'p', 'y'), ('ms', 'pyy'),
           ('ms', 'py', 'y'), ('ms', 'p', 'yy'), ('ms', 'p', 'y', 'y'),
           ('myy', 'ps'), ('myy', 'p', 's'), ('my', 'psy'), ('my', 'ps', 'y'),
           ('my', 'py', 's'), ('my', 'p', 'sy'), ('my', 'p', 's', 'y'),
           ('m', 'psyy'), ('m', 'psy', 'y'), ('m', 'ps', 'yy'),
           ('m', 'ps', 'y', 'y'), ('m', 'pyy', 's'), ('m', 'py', 'sy'),
           ('m', 'py', 's', 'y'), ('m', 'p', 'syy'),
           ('m', 'p', 'sy', 'y'), ('m', 'p', 's', 'yy'),
           ('m', 'p', 's', 'y', 'y')]
    assert list(tuple("".join(part) for part in p)
                for p in multiset_partitions('sympy')) == ans
    factorings = [[24], [8, 3], [12, 2], [4, 6], [4, 2, 3],
                  [6, 2, 2], [2, 2, 2, 3]]
    assert list(factoring_visitor(p, [2,3]) for
                p in multiset_partitions_taocp([3, 1])) == factorings

def test_multiset_combinations():
    ans = ['iii', 'iim', 'iip', 'iis', 'imp', 'ims', 'ipp', 'ips',
           'iss', 'mpp', 'mps', 'mss', 'pps', 'pss', 'sss']
    assert [''.join(i) for i in
            list(multiset_combinations('mississippi', 3))] == ans
    M = multiset('mississippi')
    assert [''.join(i) for i in
            list(multiset_combinations(M, 3))] == ans
    assert [''.join(i) for i in multiset_combinations(M, 30)] == []
    assert list(multiset_combinations([[1], [2, 3]], 2)) == [[[1], [2, 3]]]
    assert len(list(multiset_combinations('a', 3))) == 0
    assert len(list(multiset_combinations('a', 0))) == 1
    assert list(multiset_combinations('abc', 1)) == [['a'], ['b'], ['c']]


def test_multiset_permutations():
    ans = ['abby', 'abyb', 'aybb', 'baby', 'bayb', 'bbay', 'bbya', 'byab',
           'byba', 'yabb', 'ybab', 'ybba']
    assert [''.join(i) for i in multiset_permutations('baby')] == ans
    assert [''.join(i) for i in multiset_permutations(multiset('baby'))] == ans
    assert list(multiset_permutations([0, 0, 0], 2)) == [[0, 0]]
    assert list(multiset_permutations([0, 2, 1], 2)) == [
        [0, 1], [0, 2], [1, 0], [1, 2], [2, 0], [2, 1]]
    assert len(list(multiset_permutations('a', 0))) == 1
    assert len(list(multiset_permutations('a', 3))) == 0

    def test():
        for i in range(1, 7):
            print(i)
            for p in multiset_permutations([0, 0, 1, 0, 1], i):
                print(p)
    assert capture(lambda: test()) == dedent('''\
        1
        [0]
        [1]
        2
        [0, 0]
        [0, 1]
        [1, 0]
        [1, 1]
        3
        [0, 0, 0]
        [0, 0, 1]
        [0, 1, 0]
        [0, 1, 1]
        [1, 0, 0]
        [1, 0, 1]
        [1, 1, 0]
        4
        [0, 0, 0, 1]
        [0, 0, 1, 0]
        [0, 0, 1, 1]
        [0, 1, 0, 0]
        [0, 1, 0, 1]
        [0, 1, 1, 0]
        [1, 0, 0, 0]
        [1, 0, 0, 1]
        [1, 0, 1, 0]
        [1, 1, 0, 0]
        5
        [0, 0, 0, 1, 1]
        [0, 0, 1, 0, 1]
        [0, 0, 1, 1, 0]
        [0, 1, 0, 0, 1]
        [0, 1, 0, 1, 0]
        [0, 1, 1, 0, 0]
        [1, 0, 0, 0, 1]
        [1, 0, 0, 1, 0]
        [1, 0, 1, 0, 0]
        [1, 1, 0, 0, 0]
        6\n''')


def test_partitions():
    ans = [[{}], [(0, {})]]
    for i in range(2):
        assert list(partitions(0, size=i)) == ans[i]
        assert list(partitions(1, 0, size=i)) == ans[i]
        assert list(partitions(6, 2, 2, size=i)) == ans[i]
        assert list(partitions(6, 2, None, size=i)) != ans[i]
        assert list(partitions(6, None, 2, size=i)) != ans[i]
        assert list(partitions(6, 2, 0, size=i)) == ans[i]

    assert [p.copy() for p in partitions(6, k=2)] == [
        {2: 3}, {1: 2, 2: 2}, {1: 4, 2: 1}, {1: 6}]

    assert [p.copy() for p in partitions(6, k=3)] == [
        {3: 2}, {1: 1, 2: 1, 3: 1}, {1: 3, 3: 1}, {2: 3}, {1: 2, 2: 2},
        {1: 4, 2: 1}, {1: 6}]

    assert [p.copy() for p in partitions(8, k=4, m=3)] == [
        {4: 2}, {1: 1, 3: 1, 4: 1}, {2: 2, 4: 1}, {2: 1, 3: 2}] == [
        i.copy() for i in partitions(8, k=4, m=3) if all(k <= 4 for k in i)
        and sum(i.values()) <=3]

    assert [p.copy() for p in partitions(S(3), m=2)] == [
        {3: 1}, {1: 1, 2: 1}]

    assert [i.copy() for i in partitions(4, k=3)] == [
        {1: 1, 3: 1}, {2: 2}, {1: 2, 2: 1}, {1: 4}] == [
        i.copy() for i in partitions(4) if all(k <= 3 for k in i)]


    # Consistency check on output of _partitions and RGS_unrank.
    # This provides a sanity test on both routines.  Also verifies that
    # the total number of partitions is the same in each case.
    #    (from pkrathmann2)

    for n in range(2, 6):
        i  = 0
        for m, q  in _set_partitions(n):
            assert  q == RGS_unrank(i, n)
            i += 1
        assert i == RGS_enum(n)

def test_binary_partitions():
    assert [i[:] for i in binary_partitions(10)] == [[8, 2], [8, 1, 1],
        [4, 4, 2], [4, 4, 1, 1], [4, 2, 2, 2], [4, 2, 2, 1, 1],
        [4, 2, 1, 1, 1, 1], [4, 1, 1, 1, 1, 1, 1], [2, 2, 2, 2, 2],
        [2, 2, 2, 2, 1, 1], [2, 2, 2, 1, 1, 1, 1], [2, 2, 1, 1, 1, 1, 1, 1],
        [2, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]

    assert len([j[:] for j in binary_partitions(16)]) == 36


def test_bell_perm():
    assert [len(set(generate_bell(i))) for i in range(1, 7)] == [
        factorial(i) for i in range(1, 7)]
    assert list(generate_bell(3)) == [
        (0, 1, 2), (0, 2, 1), (2, 0, 1), (2, 1, 0), (1, 2, 0), (1, 0, 2)]
    # generate_bell and trotterjohnson are advertised to return the same
    # permutations; this is not technically necessary so this test could
    # be removed
    for n in range(1, 5):
        p = Permutation(range(n))
        b = generate_bell(n)
        for bi in b:
            assert bi == tuple(p.array_form)
            p = p.next_trotterjohnson()
    raises(ValueError, lambda: list(generate_bell(0)))  # XXX is this consistent with other permutation algorithms?


def test_involutions():
    lengths = [1, 2, 4, 10, 26, 76]
    for n, N in enumerate(lengths):
        i = list(generate_involutions(n + 1))
        assert len(i) == N
        assert len({Permutation(j)**2 for j in i}) == 1


def test_derangements():
    assert len(list(generate_derangements(list(range(6))))) == 265
    assert ''.join(''.join(i) for i in generate_derangements('abcde')) == (
    'badecbaecdbcaedbcdeabceadbdaecbdeacbdecabeacdbedacbedcacabedcadebcaebd'
    'cdaebcdbeacdeabcdebaceabdcebadcedabcedbadabecdaebcdaecbdcaebdcbeadceab'
    'dcebadeabcdeacbdebacdebcaeabcdeadbceadcbecabdecbadecdabecdbaedabcedacb'
    'edbacedbca')
    assert list(generate_derangements([0, 1, 2, 3])) == [
        [1, 0, 3, 2], [1, 2, 3, 0], [1, 3, 0, 2], [2, 0, 3, 1],
        [2, 3, 0, 1], [2, 3, 1, 0], [3, 0, 1, 2], [3, 2, 0, 1], [3, 2, 1, 0]]
    assert list(generate_derangements([0, 1, 2, 2])) == [
        [2, 2, 0, 1], [2, 2, 1, 0]]


def test_necklaces():
    def count(n, k, f):
        return len(list(necklaces(n, k, f)))
    m = []
    for i in range(1, 8):
        m.append((
        i, count(i, 2, 0), count(i, 2, 1), count(i, 3, 1)))
    assert Matrix(m) == Matrix([
        [1,   2,   2,   3],
        [2,   3,   3,   6],
        [3,   4,   4,  10],
        [4,   6,   6,  21],
        [5,   8,   8,  39],
        [6,  14,  13,  92],
        [7,  20,  18, 198]])

def test_bracelets():
    bc = [i for i in bracelets(2, 4)]
    assert Matrix(bc) == Matrix([
        [0, 0],
        [0, 1],
        [0, 2],
        [0, 3],
        [1, 1],
        [1, 2],
        [1, 3],
        [2, 2],
        [2, 3],
        [3, 3]
        ])
    bc = [i for i in bracelets(4, 2)]
    assert Matrix(bc) == Matrix([
        [0, 0, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 1],
        [0, 1, 0, 1],
        [0, 1, 1, 1],
        [1, 1, 1, 1]
    ])


def test_generate_oriented_forest():
    assert list(generate_oriented_forest(5)) == [[0, 1, 2, 3, 4],
        [0, 1, 2, 3, 3], [0, 1, 2, 3, 2], [0, 1, 2, 3, 1], [0, 1, 2, 3, 0],
        [0, 1, 2, 2, 2], [0, 1, 2, 2, 1], [0, 1, 2, 2, 0], [0, 1, 2, 1, 2],
        [0, 1, 2, 1, 1], [0, 1, 2, 1, 0], [0, 1, 2, 0, 1], [0, 1, 2, 0, 0],
        [0, 1, 1, 1, 1], [0, 1, 1, 1, 0], [0, 1, 1, 0, 1], [0, 1, 1, 0, 0],
        [0, 1, 0, 1, 0], [0, 1, 0, 0, 0], [0, 0, 0, 0, 0]]
    assert len(list(generate_oriented_forest(10))) == 1842


def test_unflatten():
    r = list(range(10))
    assert unflatten(r) == list(zip(r[::2], r[1::2]))
    assert unflatten(r, 5) == [tuple(r[:5]), tuple(r[5:])]
    raises(ValueError, lambda: unflatten(list(range(10)), 3))
    raises(ValueError, lambda: unflatten(list(range(10)), -2))


def test_common_prefix_suffix():
    assert common_prefix([], [1]) == []
    assert common_prefix(list(range(3))) == [0, 1, 2]
    assert common_prefix(list(range(3)), list(range(4))) == [0, 1, 2]
    assert common_prefix([1, 2, 3], [1, 2, 5]) == [1, 2]
    assert common_prefix([1, 2, 3], [1, 3, 5]) == [1]

    assert common_suffix([], [1]) == []
    assert common_suffix(list(range(3))) == [0, 1, 2]
    assert common_suffix(list(range(3)), list(range(3))) == [0, 1, 2]
    assert common_suffix(list(range(3)), list(range(4))) == []
    assert common_suffix([1, 2, 3], [9, 2, 3]) == [2, 3]
    assert common_suffix([1, 2, 3], [9, 7, 3]) == [3]


def test_minlex():
    assert minlex([1, 2, 0]) == (0, 1, 2)
    assert minlex((1, 2, 0)) == (0, 1, 2)
    assert minlex((1, 0, 2)) == (0, 2, 1)
    assert minlex((1, 0, 2), directed=False) == (0, 1, 2)
    assert minlex('aba') == 'aab'


def test_ordered():
    assert list(ordered((x, y), hash, default=False)) in [[x, y], [y, x]]
    assert list(ordered((x, y), hash, default=False)) == \
        list(ordered((y, x), hash, default=False))
    assert list(ordered((x, y))) == [x, y]

    seq, keys = [[[1, 2, 1], [0, 3, 1], [1, 1, 3], [2], [1]],
                 (lambda x: len(x), lambda x: sum(x))]
    assert list(ordered(seq, keys, default=False, warn=False)) == \
        [[1], [2], [1, 2, 1], [0, 3, 1], [1, 1, 3]]
    raises(ValueError, lambda:
           list(ordered(seq, keys, default=False, warn=True)))


def test_runs():
    assert runs([]) == []
    assert runs([1]) == [[1]]
    assert runs([1, 1]) == [[1], [1]]
    assert runs([1, 1, 2]) == [[1], [1, 2]]
    assert runs([1, 2, 1]) == [[1, 2], [1]]
    assert runs([2, 1, 1]) == [[2], [1], [1]]
    from operator import lt
    assert runs([2, 1, 1], lt) == [[2, 1], [1]]


def test_reshape():
    seq = list(range(1, 9))
    assert reshape(seq, [4]) == \
        [[1, 2, 3, 4], [5, 6, 7, 8]]
    assert reshape(seq, (4,)) == \
        [(1, 2, 3, 4), (5, 6, 7, 8)]
    assert reshape(seq, (2, 2)) == \
        [(1, 2, 3, 4), (5, 6, 7, 8)]
    assert reshape(seq, (2, [2])) == \
        [(1, 2, [3, 4]), (5, 6, [7, 8])]
    assert reshape(seq, ((2,), [2])) == \
        [((1, 2), [3, 4]), ((5, 6), [7, 8])]
    assert reshape(seq, (1, [2], 1)) == \
        [(1, [2, 3], 4), (5, [6, 7], 8)]
    assert reshape(tuple(seq), ([[1], 1, (2,)],)) == \
        (([[1], 2, (3, 4)],), ([[5], 6, (7, 8)],))
    assert reshape(tuple(seq), ([1], 1, (2,))) == \
        (([1], 2, (3, 4)), ([5], 6, (7, 8)))
    assert reshape(list(range(12)), [2, [3], {2}, (1, (3,), 1)]) == \
        [[0, 1, [2, 3, 4], {5, 6}, (7, (8, 9, 10), 11)]]
    raises(ValueError, lambda: reshape([0, 1], [-1]))
    raises(ValueError, lambda: reshape([0, 1], [3]))

def test_uniq():
    assert list(uniq(p.copy() for p in partitions(4))) == \
        [{4: 1}, {1: 1, 3: 1}, {2: 2}, {1: 2, 2: 1}, {1: 4}]
    assert list(uniq(x % 2 for x in range(5))) == [0, 1]
    assert list(uniq('a')) == ['a']
    assert list(uniq('ababc')) == list('abc')
    assert list(uniq([[1], [2, 1], [1]])) == [[1], [2, 1]]
    assert list(uniq(permutations(i for i in [[1], 2, 2]))) == \
        [([1], 2, 2), (2, [1], 2), (2, 2, [1])]
    assert list(uniq([2, 3, 2, 4, [2], [1], [2], [3], [1]])) == \
        [2, 3, 4, [2], [1], [3]]


def test_kbins():
    assert len(list(kbins('1123', 2, ordered=1))) == 24
    assert len(list(kbins('1123', 2, ordered=11))) == 36
    assert len(list(kbins('1123', 2, ordered=10))) == 10
    assert len(list(kbins('1123', 2, ordered=0))) == 5
    assert len(list(kbins('1123', 2, ordered=None))) == 3

    def test():
        for ordered in [None, 0, 1, 10, 11]:
            print('ordered =', ordered)
            for p in kbins([0, 0, 1], 2, ordered=ordered):
                print('   ', p)
    assert capture(lambda : test()) == dedent('''\
        ordered = None
            [[0], [0, 1]]
            [[0, 0], [1]]
        ordered = 0
            [[0, 0], [1]]
            [[0, 1], [0]]
        ordered = 1
            [[0], [0, 1]]
            [[0], [1, 0]]
            [[1], [0, 0]]
        ordered = 10
            [[0, 0], [1]]
            [[1], [0, 0]]
            [[0, 1], [0]]
            [[0], [0, 1]]
        ordered = 11
            [[0], [0, 1]]
            [[0, 0], [1]]
            [[0], [1, 0]]
            [[0, 1], [0]]
            [[1], [0, 0]]
            [[1, 0], [0]]\n''')

    def test():
        for ordered in [None, 0, 1, 10, 11]:
            print('ordered =', ordered)
            for p in kbins(list(range(3)), 2, ordered=ordered):
                print('   ', p)
    assert capture(lambda : test()) == dedent('''\
        ordered = None
            [[0], [1, 2]]
            [[0, 1], [2]]
        ordered = 0
            [[0, 1], [2]]
            [[0, 2], [1]]
            [[0], [1, 2]]
        ordered = 1
            [[0], [1, 2]]
            [[0], [2, 1]]
            [[1], [0, 2]]
            [[1], [2, 0]]
            [[2], [0, 1]]
            [[2], [1, 0]]
        ordered = 10
            [[0, 1], [2]]
            [[2], [0, 1]]
            [[0, 2], [1]]
            [[1], [0, 2]]
            [[0], [1, 2]]
            [[1, 2], [0]]
        ordered = 11
            [[0], [1, 2]]
            [[0, 1], [2]]
            [[0], [2, 1]]
            [[0, 2], [1]]
            [[1], [0, 2]]
            [[1, 0], [2]]
            [[1], [2, 0]]
            [[1, 2], [0]]
            [[2], [0, 1]]
            [[2, 0], [1]]
            [[2], [1, 0]]
            [[2, 1], [0]]\n''')


def test_has_dups():
    assert has_dups(set()) is False
    assert has_dups(list(range(3))) is False
    assert has_dups([1, 2, 1]) is True


def test__partition():
    assert _partition('abcde', [1, 0, 1, 2, 0]) == [
        ['b', 'e'], ['a', 'c'], ['d']]
    assert _partition('abcde', [1, 0, 1, 2, 0], 3) == [
        ['b', 'e'], ['a', 'c'], ['d']]
    output = (3, [1, 0, 1, 2, 0])
    assert _partition('abcde', *output) == [['b', 'e'], ['a', 'c'], ['d']]


def test_ordered_partitions():
    from sympy.functions.combinatorial.numbers import nT
    f = ordered_partitions
    assert list(f(0, 1)) == [[]]
    assert list(f(1, 0)) == [[]]
    for i in range(1, 7):
        for j in [None] + list(range(1, i)):
            assert (
                sum(1 for p in f(i, j, 1)) ==
                sum(1 for p in f(i, j, 0)) ==
                nT(i, j))


def test_rotations():
    assert list(rotations('ab')) == [['a', 'b'], ['b', 'a']]
    assert list(rotations(range(3))) == [[0, 1, 2], [1, 2, 0], [2, 0, 1]]
    assert list(rotations(range(3), dir=-1)) == [[0, 1, 2], [2, 0, 1], [1, 2, 0]]


def test_ibin():
    assert ibin(3) == [1, 1]
    assert ibin(3, 3) == [0, 1, 1]
    assert ibin(3, str=True) == '11'
    assert ibin(3, 3, str=True) == '011'
    assert list(ibin(2, 'all')) == [(0, 0), (0, 1), (1, 0), (1, 1)]
    assert list(ibin(2, 'all', str=True)) == ['00', '01', '10', '11']
