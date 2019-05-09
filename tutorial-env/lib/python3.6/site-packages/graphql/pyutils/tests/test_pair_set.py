from graphql.pyutils.pair_set import PairSet


def test_pair_set():
    ps = PairSet()
    are_mutually_exclusive = True

    ps.add(1, 2, are_mutually_exclusive)
    ps.add(2, 4, are_mutually_exclusive)

    assert ps.has(1, 2, are_mutually_exclusive)
    assert ps.has(2, 1, are_mutually_exclusive)
    assert not ps.has(1, 2, not are_mutually_exclusive)
    assert not ps.has(2, 1, not are_mutually_exclusive)

    assert (1, 2, are_mutually_exclusive) in ps
    assert (2, 1, are_mutually_exclusive) in ps
    assert (1, 2, (not are_mutually_exclusive)) not in ps
    assert (2, 1, (not are_mutually_exclusive)) not in ps

    assert ps.has(4, 2, are_mutually_exclusive)
    assert ps.has(2, 4, are_mutually_exclusive)

    assert not ps.has(2, 3, are_mutually_exclusive)
    assert not ps.has(1, 3, are_mutually_exclusive)

    assert ps.has(4, 2, are_mutually_exclusive)
    assert ps.has(2, 4, are_mutually_exclusive)


def test_pair_set_not_mutually_exclusive():
    ps = PairSet()
    are_mutually_exclusive = False

    ps.add(1, 2, are_mutually_exclusive)

    assert ps.has(1, 2, are_mutually_exclusive)
    assert ps.has(2, 1, are_mutually_exclusive)

    assert ps.has(1, 2, not are_mutually_exclusive)
    assert ps.has(2, 1, not are_mutually_exclusive)
