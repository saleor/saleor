from sympy.core.compatibility import range
from sympy.combinatorics.partitions import (Partition, IntegerPartition,
                                            RGS_enum, RGS_unrank, RGS_rank,
                                            random_integer_partition)
from sympy.utilities.pytest import raises
from sympy.utilities.iterables import default_sort_key, partitions


def test_partition():
    from sympy.abc import x

    raises(ValueError, lambda: Partition(*list(range(3))))
    raises(ValueError, lambda: Partition([1, 1, 2]))

    a = Partition([1, 2, 3], [4])
    b = Partition([1, 2], [3, 4])
    c = Partition([x])
    l = [a, b, c]
    l.sort(key=default_sort_key)
    assert l == [c, a, b]
    l.sort(key=lambda w: default_sort_key(w, order='rev-lex'))
    assert l == [c, a, b]

    assert (a == b) is False
    assert a <= b
    assert (a > b) is False
    assert a != b
    assert a < b

    assert (a + 2).partition == [[1, 2], [3, 4]]
    assert (b - 1).partition == [[1, 2, 4], [3]]

    assert (a - 1).partition == [[1, 2, 3, 4]]
    assert (a + 1).partition == [[1, 2, 4], [3]]
    assert (b + 1).partition == [[1, 2], [3], [4]]

    assert a.rank == 1
    assert b.rank == 3

    assert a.RGS == (0, 0, 0, 1)
    assert b.RGS == (0, 0, 1, 1)


def test_integer_partition():
    # no zeros in partition
    raises(ValueError, lambda: IntegerPartition(list(range(3))))
    # check fails since 1 + 2 != 100
    raises(ValueError, lambda: IntegerPartition(100, list(range(1, 3))))
    a = IntegerPartition(8, [1, 3, 4])
    b = a.next_lex()
    c = IntegerPartition([1, 3, 4])
    d = IntegerPartition(8, {1: 3, 3: 1, 2: 1})
    assert a == c
    assert a.integer == d.integer
    assert a.conjugate == [3, 2, 2, 1]
    assert (a == b) is False
    assert a <= b
    assert (a > b) is False
    assert a != b

    for i in range(1, 11):
        next = set()
        prev = set()
        a = IntegerPartition([i])
        ans = {IntegerPartition(p) for p in partitions(i)}
        n = len(ans)
        for j in range(n):
            next.add(a)
            a = a.next_lex()
            IntegerPartition(i, a.partition)  # check it by giving i
        for j in range(n):
            prev.add(a)
            a = a.prev_lex()
            IntegerPartition(i, a.partition)  # check it by giving i
        assert next == ans
        assert prev == ans

    assert IntegerPartition([1, 2, 3]).as_ferrers() == '###\n##\n#'
    assert IntegerPartition([1, 1, 3]).as_ferrers('o') == 'ooo\no\no'
    assert str(IntegerPartition([1, 1, 3])) == '[3, 1, 1]'
    assert IntegerPartition([1, 1, 3]).partition == [3, 1, 1]

    raises(ValueError, lambda: random_integer_partition(-1))
    assert random_integer_partition(1) == [1]
    assert random_integer_partition(10, seed=[1, 3, 2, 1, 5, 1]
            ) == [5, 2, 1, 1, 1]


def test_rgs():
    raises(ValueError, lambda: RGS_unrank(-1, 3))
    raises(ValueError, lambda: RGS_unrank(3, 0))
    raises(ValueError, lambda: RGS_unrank(10, 1))

    raises(ValueError, lambda: Partition.from_rgs(list(range(3)), list(range(2))))
    raises(ValueError, lambda: Partition.from_rgs(list(range(1, 3)), list(range(2))))
    assert RGS_enum(-1) == 0
    assert RGS_enum(1) == 1
    assert RGS_unrank(7, 5) == [0, 0, 1, 0, 2]
    assert RGS_unrank(23, 14) == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 2, 2]
    assert RGS_rank(RGS_unrank(40, 100)) == 40
