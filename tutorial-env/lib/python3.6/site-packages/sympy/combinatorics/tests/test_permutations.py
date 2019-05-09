from itertools import permutations

from sympy.core.compatibility import range
from sympy.core.symbol import Symbol
from sympy.combinatorics.permutations import (Permutation, _af_parity,
    _af_rmul, _af_rmuln, Cycle)
from sympy.utilities.pytest import raises

rmul = Permutation.rmul
a = Symbol('a', integer=True)


def test_Permutation():
    # don't auto fill 0
    raises(ValueError, lambda: Permutation([1]))
    p = Permutation([0, 1, 2, 3])
    # call as bijective
    assert [p(i) for i in range(p.size)] == list(p)
    # call as operator
    assert p(list(range(p.size))) == list(p)
    # call as function
    assert list(p(1, 2)) == [0, 2, 1, 3]
    # conversion to list
    assert list(p) == list(range(4))
    assert Permutation(size=4) == Permutation(3)
    assert Permutation(Permutation(3), size=5) == Permutation(4)
    # cycle form with size
    assert Permutation([[1, 2]], size=4) == Permutation([[1, 2], [0], [3]])
    # random generation
    assert Permutation.random(2) in (Permutation([1, 0]), Permutation([0, 1]))

    p = Permutation([2, 5, 1, 6, 3, 0, 4])
    q = Permutation([[1], [0, 3, 5, 6, 2, 4]])
    assert len({p, p}) == 1
    r = Permutation([1, 3, 2, 0, 4, 6, 5])
    ans = Permutation(_af_rmuln(*[w.array_form for w in (p, q, r)])).array_form
    assert rmul(p, q, r).array_form == ans
    # make sure no other permutation of p, q, r could have given
    # that answer
    for a, b, c in permutations((p, q, r)):
        if (a, b, c) == (p, q, r):
            continue
        assert rmul(a, b, c).array_form != ans

    assert p.support() == list(range(7))
    assert q.support() == [0, 2, 3, 4, 5, 6]
    assert Permutation(p.cyclic_form).array_form == p.array_form
    assert p.cardinality == 5040
    assert q.cardinality == 5040
    assert q.cycles == 2
    assert rmul(q, p) == Permutation([4, 6, 1, 2, 5, 3, 0])
    assert rmul(p, q) == Permutation([6, 5, 3, 0, 2, 4, 1])
    assert _af_rmul(p.array_form, q.array_form) == \
        [6, 5, 3, 0, 2, 4, 1]

    assert rmul(Permutation([[1, 2, 3], [0, 4]]),
                Permutation([[1, 2, 4], [0], [3]])).cyclic_form == \
        [[0, 4, 2], [1, 3]]
    assert q.array_form == [3, 1, 4, 5, 0, 6, 2]
    assert q.cyclic_form == [[0, 3, 5, 6, 2, 4]]
    assert q.full_cyclic_form == [[0, 3, 5, 6, 2, 4], [1]]
    assert p.cyclic_form == [[0, 2, 1, 5], [3, 6, 4]]
    t = p.transpositions()
    assert t == [(0, 5), (0, 1), (0, 2), (3, 4), (3, 6)]
    assert Permutation.rmul(*[Permutation(Cycle(*ti)) for ti in (t)])
    assert Permutation([1, 0]).transpositions() == [(0, 1)]

    assert p**13 == p
    assert q**0 == Permutation(list(range(q.size)))
    assert q**-2 == ~q**2
    assert q**2 == Permutation([5, 1, 0, 6, 3, 2, 4])
    assert q**3 == q**2*q
    assert q**4 == q**2*q**2

    a = Permutation(1, 3)
    b = Permutation(2, 0, 3)
    I = Permutation(3)
    assert ~a == a**-1
    assert a*~a == I
    assert a*b**-1 == a*~b

    ans = Permutation(0, 5, 3, 1, 6)(2, 4)
    assert (p + q.rank()).rank() == ans.rank()
    assert (p + q.rank())._rank == ans.rank()
    assert (q + p.rank()).rank() == ans.rank()
    raises(TypeError, lambda: p + Permutation(list(range(10))))

    assert (p - q.rank()).rank() == Permutation(0, 6, 3, 1, 2, 5, 4).rank()
    assert p.rank() - q.rank() < 0  # for coverage: make sure mod is used
    assert (q - p.rank()).rank() == Permutation(1, 4, 6, 2)(3, 5).rank()

    assert p*q == Permutation(_af_rmuln(*[list(w) for w in (q, p)]))
    assert p*Permutation([]) == p
    assert Permutation([])*p == p
    assert p*Permutation([[0, 1]]) == Permutation([2, 5, 0, 6, 3, 1, 4])
    assert Permutation([[0, 1]])*p == Permutation([5, 2, 1, 6, 3, 0, 4])

    pq = p ^ q
    assert pq == Permutation([5, 6, 0, 4, 1, 2, 3])
    assert pq == rmul(q, p, ~q)
    qp = q ^ p
    assert qp == Permutation([4, 3, 6, 2, 1, 5, 0])
    assert qp == rmul(p, q, ~p)
    raises(ValueError, lambda: p ^ Permutation([]))

    assert p.commutator(q) == Permutation(0, 1, 3, 4, 6, 5, 2)
    assert q.commutator(p) == Permutation(0, 2, 5, 6, 4, 3, 1)
    assert p.commutator(q) == ~q.commutator(p)
    raises(ValueError, lambda: p.commutator(Permutation([])))

    assert len(p.atoms()) == 7
    assert q.atoms() == {0, 1, 2, 3, 4, 5, 6}

    assert p.inversion_vector() == [2, 4, 1, 3, 1, 0]
    assert q.inversion_vector() == [3, 1, 2, 2, 0, 1]

    assert Permutation.from_inversion_vector(p.inversion_vector()) == p
    assert Permutation.from_inversion_vector(q.inversion_vector()).array_form\
        == q.array_form
    raises(ValueError, lambda: Permutation.from_inversion_vector([0, 2]))
    assert Permutation([i for i in range(500, -1, -1)]).inversions() == 125250

    s = Permutation([0, 4, 1, 3, 2])
    assert s.parity() == 0
    _ = s.cyclic_form  # needed to create a value for _cyclic_form
    assert len(s._cyclic_form) != s.size and s.parity() == 0
    assert not s.is_odd
    assert s.is_even
    assert Permutation([0, 1, 4, 3, 2]).parity() == 1
    assert _af_parity([0, 4, 1, 3, 2]) == 0
    assert _af_parity([0, 1, 4, 3, 2]) == 1

    s = Permutation([0])

    assert s.is_Singleton
    assert Permutation([]).is_Empty

    r = Permutation([3, 2, 1, 0])
    assert (r**2).is_Identity

    assert rmul(~p, p).is_Identity
    assert (~p)**13 == Permutation([5, 2, 0, 4, 6, 1, 3])
    assert ~(r**2).is_Identity
    assert p.max() == 6
    assert p.min() == 0

    q = Permutation([[6], [5], [0, 1, 2, 3, 4]])

    assert q.max() == 4
    assert q.min() == 0

    p = Permutation([1, 5, 2, 0, 3, 6, 4])
    q = Permutation([[1, 2, 3, 5, 6], [0, 4]])

    assert p.ascents() == [0, 3, 4]
    assert q.ascents() == [1, 2, 4]
    assert r.ascents() == []

    assert p.descents() == [1, 2, 5]
    assert q.descents() == [0, 3, 5]
    assert Permutation(r.descents()).is_Identity

    assert p.inversions() == 7
    # test the merge-sort with a longer permutation
    big = list(p) + list(range(p.max() + 1, p.max() + 130))
    assert Permutation(big).inversions() == 7
    assert p.signature() == -1
    assert q.inversions() == 11
    assert q.signature() == -1
    assert rmul(p, ~p).inversions() == 0
    assert rmul(p, ~p).signature() == 1

    assert p.order() == 6
    assert q.order() == 10
    assert (p**(p.order())).is_Identity

    assert p.length() == 6
    assert q.length() == 7
    assert r.length() == 4

    assert p.runs() == [[1, 5], [2], [0, 3, 6], [4]]
    assert q.runs() == [[4], [2, 3, 5], [0, 6], [1]]
    assert r.runs() == [[3], [2], [1], [0]]

    assert p.index() == 8
    assert q.index() == 8
    assert r.index() == 3

    assert p.get_precedence_distance(q) == q.get_precedence_distance(p)
    assert p.get_adjacency_distance(q) == p.get_adjacency_distance(q)
    assert p.get_positional_distance(q) == p.get_positional_distance(q)
    p = Permutation([0, 1, 2, 3])
    q = Permutation([3, 2, 1, 0])
    assert p.get_precedence_distance(q) == 6
    assert p.get_adjacency_distance(q) == 3
    assert p.get_positional_distance(q) == 8
    p = Permutation([0, 3, 1, 2, 4])
    q = Permutation.josephus(4, 5, 2)
    assert p.get_adjacency_distance(q) == 3
    raises(ValueError, lambda: p.get_adjacency_distance(Permutation([])))
    raises(ValueError, lambda: p.get_positional_distance(Permutation([])))
    raises(ValueError, lambda: p.get_precedence_distance(Permutation([])))

    a = [Permutation.unrank_nonlex(4, i) for i in range(5)]
    iden = Permutation([0, 1, 2, 3])
    for i in range(5):
        for j in range(i + 1, 5):
            assert a[i].commutes_with(a[j]) == \
                (rmul(a[i], a[j]) == rmul(a[j], a[i]))
            if a[i].commutes_with(a[j]):
                assert a[i].commutator(a[j]) == iden
                assert a[j].commutator(a[i]) == iden

    a = Permutation(3)
    b = Permutation(0, 6, 3)(1, 2)
    assert a.cycle_structure == {1: 4}
    assert b.cycle_structure == {2: 1, 3: 1, 1: 2}


def test_Permutation_subclassing():
    # Subclass that adds permutation application on iterables
    class CustomPermutation(Permutation):
        def __call__(self, *i):
            try:
                return super(CustomPermutation, self).__call__(*i)
            except TypeError:
                pass

            try:
                perm_obj = i[0]
                return [self._array_form[j] for j in perm_obj]
            except Exception:
                raise TypeError('unrecognized argument')

        def __eq__(self, other):
            if isinstance(other, Permutation):
                return self._hashable_content() == other._hashable_content()
            else:
                return super(CustomPermutation, self).__eq__(other)

        def __hash__(self):
            return super(CustomPermutation, self).__hash__()

    p = CustomPermutation([1, 2, 3, 0])
    q = Permutation([1, 2, 3, 0])

    assert p == q
    raises(TypeError, lambda: q([1, 2]))
    assert [2, 3] == p([1, 2])

    assert type(p * q) == CustomPermutation
    assert type(q * p) == Permutation  # True because q.__mul__(p) is called!

    # Run all tests for the Permutation class also on the subclass
    def wrapped_test_Permutation():
        # Monkeypatch the class definition in the globals
        globals()['__Perm'] = globals()['Permutation']
        globals()['Permutation'] = CustomPermutation
        test_Permutation()
        globals()['Permutation'] = globals()['__Perm']  # Restore
        del globals()['__Perm']

    wrapped_test_Permutation()


def test_josephus():
    assert Permutation.josephus(4, 6, 1) == Permutation([3, 1, 0, 2, 5, 4])
    assert Permutation.josephus(1, 5, 1).is_Identity


def test_ranking():
    assert Permutation.unrank_lex(5, 10).rank() == 10
    p = Permutation.unrank_lex(15, 225)
    assert p.rank() == 225
    p1 = p.next_lex()
    assert p1.rank() == 226
    assert Permutation.unrank_lex(15, 225).rank() == 225
    assert Permutation.unrank_lex(10, 0).is_Identity
    p = Permutation.unrank_lex(4, 23)
    assert p.rank() == 23
    assert p.array_form == [3, 2, 1, 0]
    assert p.next_lex() is None

    p = Permutation([1, 5, 2, 0, 3, 6, 4])
    q = Permutation([[1, 2, 3, 5, 6], [0, 4]])
    a = [Permutation.unrank_trotterjohnson(4, i).array_form for i in range(5)]
    assert a == [[0, 1, 2, 3], [0, 1, 3, 2], [0, 3, 1, 2], [3, 0, 1,
        2], [3, 0, 2, 1] ]
    assert [Permutation(pa).rank_trotterjohnson() for pa in a] == list(range(5))
    assert Permutation([0, 1, 2, 3]).next_trotterjohnson() == \
        Permutation([0, 1, 3, 2])

    assert q.rank_trotterjohnson() == 2283
    assert p.rank_trotterjohnson() == 3389
    assert Permutation([1, 0]).rank_trotterjohnson() == 1
    a = Permutation(list(range(3)))
    b = a
    l = []
    tj = []
    for i in range(6):
        l.append(a)
        tj.append(b)
        a = a.next_lex()
        b = b.next_trotterjohnson()
    assert a == b is None
    assert {tuple(a) for a in l} == {tuple(a) for a in tj}

    p = Permutation([2, 5, 1, 6, 3, 0, 4])
    q = Permutation([[6], [5], [0, 1, 2, 3, 4]])
    assert p.rank() == 1964
    assert q.rank() == 870
    assert Permutation([]).rank_nonlex() == 0
    prank = p.rank_nonlex()
    assert prank == 1600
    assert Permutation.unrank_nonlex(7, 1600) == p
    qrank = q.rank_nonlex()
    assert qrank == 41
    assert Permutation.unrank_nonlex(7, 41) == Permutation(q.array_form)

    a = [Permutation.unrank_nonlex(4, i).array_form for i in range(24)]
    assert a == [
        [1, 2, 3, 0], [3, 2, 0, 1], [1, 3, 0, 2], [1, 2, 0, 3], [2, 3, 1, 0],
        [2, 0, 3, 1], [3, 0, 1, 2], [2, 0, 1, 3], [1, 3, 2, 0], [3, 0, 2, 1],
        [1, 0, 3, 2], [1, 0, 2, 3], [2, 1, 3, 0], [2, 3, 0, 1], [3, 1, 0, 2],
        [2, 1, 0, 3], [3, 2, 1, 0], [0, 2, 3, 1], [0, 3, 1, 2], [0, 2, 1, 3],
        [3, 1, 2, 0], [0, 3, 2, 1], [0, 1, 3, 2], [0, 1, 2, 3]]

    N = 10
    p1 = Permutation(a[0])
    for i in range(1, N+1):
        p1 = p1*Permutation(a[i])
    p2 = Permutation.rmul_with_af(*[Permutation(h) for h in a[N::-1]])
    assert p1 == p2

    ok = []
    p = Permutation([1, 0])
    for i in range(3):
        ok.append(p.array_form)
        p = p.next_nonlex()
        if p is None:
            ok.append(None)
            break
    assert ok == [[1, 0], [0, 1], None]
    assert Permutation([3, 2, 0, 1]).next_nonlex() == Permutation([1, 3, 0, 2])
    assert [Permutation(pa).rank_nonlex() for pa in a] == list(range(24))


def test_mul():
    a, b = [0, 2, 1, 3], [0, 1, 3, 2]
    assert _af_rmul(a, b) == [0, 2, 3, 1]
    assert _af_rmuln(a, b, list(range(4))) == [0, 2, 3, 1]
    assert rmul(Permutation(a), Permutation(b)).array_form == [0, 2, 3, 1]

    a = Permutation([0, 2, 1, 3])
    b = (0, 1, 3, 2)
    c = (3, 1, 2, 0)
    assert Permutation.rmul(a, b, c) == Permutation([1, 2, 3, 0])
    assert Permutation.rmul(a, c) == Permutation([3, 2, 1, 0])
    raises(TypeError, lambda: Permutation.rmul(b, c))

    n = 6
    m = 8
    a = [Permutation.unrank_nonlex(n, i).array_form for i in range(m)]
    h = list(range(n))
    for i in range(m):
        h = _af_rmul(h, a[i])
        h2 = _af_rmuln(*a[:i + 1])
        assert h == h2


def test_args():
    p = Permutation([(0, 3, 1, 2), (4, 5)])
    assert p._cyclic_form is None
    assert Permutation(p) == p
    assert p.cyclic_form == [[0, 3, 1, 2], [4, 5]]
    assert p._array_form == [3, 2, 0, 1, 5, 4]
    p = Permutation((0, 3, 1, 2))
    assert p._cyclic_form is None
    assert p._array_form == [0, 3, 1, 2]
    assert Permutation([0]) == Permutation((0, ))
    assert Permutation([[0], [1]]) == Permutation(((0, ), (1, ))) == \
        Permutation(((0, ), [1]))
    assert Permutation([[1, 2]]) == Permutation([0, 2, 1])
    assert Permutation([[1], [4, 2]]) == Permutation([0, 1, 4, 3, 2])
    assert Permutation([[1], [4, 2]], size=1) == Permutation([0, 1, 4, 3, 2])
    assert Permutation(
        [[1], [4, 2]], size=6) == Permutation([0, 1, 4, 3, 2, 5])
    assert Permutation([[0, 1], [0, 2]]) == Permutation(0, 1, 2)
    assert Permutation([], size=3) == Permutation([0, 1, 2])
    assert Permutation(3).list(5) == [0, 1, 2, 3, 4]
    assert Permutation(3).list(-1) == []
    assert Permutation(5)(1, 2).list(-1) == [0, 2, 1]
    assert Permutation(5)(1, 2).list() == [0, 2, 1, 3, 4, 5]
    raises(ValueError, lambda: Permutation([1, 2], [0]))
           # enclosing brackets needed
    raises(ValueError, lambda: Permutation([[1, 2], 0]))
           # enclosing brackets needed on 0
    raises(ValueError, lambda: Permutation([1, 1, 0]))
    raises(ValueError, lambda: Permutation([4, 5], size=10))  # where are 0-3?
    # but this is ok because cycles imply that only those listed moved
    assert Permutation(4, 5) == Permutation([0, 1, 2, 3, 5, 4])


def test_Cycle():
    assert str(Cycle()) == '()'
    assert Cycle(Cycle(1,2)) == Cycle(1, 2)
    assert Cycle(1,2).copy() == Cycle(1,2)
    assert list(Cycle(1, 3, 2)) == [0, 3, 1, 2]
    assert Cycle(1, 2)(2, 3) == Cycle(1, 3, 2)
    assert Cycle(1, 2)(2, 3)(4, 5) == Cycle(1, 3, 2)(4, 5)
    assert Permutation(Cycle(1, 2)(2, 1, 0, 3)).cyclic_form, Cycle(0, 2, 1)
    raises(ValueError, lambda: Cycle().list())
    assert Cycle(1, 2).list() == [0, 2, 1]
    assert Cycle(1, 2).list(4) == [0, 2, 1, 3]
    assert Cycle(3).list(2) == [0, 1]
    assert Cycle(3).list(6) == [0, 1, 2, 3, 4, 5]
    assert Permutation(Cycle(1, 2), size=4) == \
        Permutation([0, 2, 1, 3])
    assert str(Cycle(1, 2)(4, 5)) == '(1 2)(4 5)'
    assert str(Cycle(1, 2)) == '(1 2)'
    assert Cycle(Permutation(list(range(3)))) == Cycle()
    assert Cycle(1, 2).list() == [0, 2, 1]
    assert Cycle(1, 2).list(4) == [0, 2, 1, 3]
    assert Cycle().size == 0
    raises(ValueError, lambda: Cycle((1, 2)))
    raises(ValueError, lambda: Cycle(1, 2, 1))
    raises(TypeError, lambda: Cycle(1, 2)*{})
    raises(ValueError, lambda: Cycle(4)[a])
    raises(ValueError, lambda: Cycle(2, -4, 3))

    # check round-trip
    p = Permutation([[1, 2], [4, 3]], size=5)
    assert Permutation(Cycle(p)) == p


def test_from_sequence():
    assert Permutation.from_sequence('SymPy') == Permutation(4)(0, 1, 3)
    assert Permutation.from_sequence('SymPy', key=lambda x: x.lower()) == \
        Permutation(4)(0, 2)(1, 3)


def test_printing_cyclic():
    Permutation.print_cyclic = True
    p1 = Permutation([0, 2, 1])
    assert repr(p1) == 'Permutation(1, 2)'
    assert str(p1) == '(1 2)'
    p2 = Permutation()
    assert repr(p2) == 'Permutation()'
    assert str(p2) == '()'
    p3 = Permutation([1, 2, 0, 3])
    assert repr(p3) == 'Permutation(3)(0, 1, 2)'


def test_printing_non_cyclic():
    Permutation.print_cyclic = False
    p1 = Permutation([0, 1, 2, 3, 4, 5])
    assert repr(p1) == 'Permutation([], size=6)'
    assert str(p1) == 'Permutation([], size=6)'
    p2 = Permutation([0, 1, 2])
    assert repr(p2) == 'Permutation([0, 1, 2])'
    assert str(p2) == 'Permutation([0, 1, 2])'

    p3 = Permutation([0, 2, 1])
    assert repr(p3) == 'Permutation([0, 2, 1])'
    assert str(p3) == 'Permutation([0, 2, 1])'
    p4 = Permutation([0, 1, 3, 2, 4, 5, 6, 7])
    assert repr(p4) == 'Permutation([0, 1, 3, 2], size=8)'
