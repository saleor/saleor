from ..cache import CacheDict


def test_capacity():
    # given
    cache = CacheDict(2)
    cache[1] = "a"
    cache[2] = "b"

    # when
    cache[3] = "c"

    # then
    assert 1 not in cache
    assert 2 in cache
    assert 3 in cache


def test_persistence():
    # given
    cache = CacheDict(2)
    watchdog = object()

    # when
    cache[1] = watchdog

    # then
    assert cache[1] is watchdog


def test_eviction_order():
    # given
    cache = CacheDict(2)
    cache[1] = "a"
    cache[2] = "b"

    # when
    cache[1]
    cache[3] = "c"

    # then
    assert 1 in cache
    assert 2 not in cache
    assert 3 in cache
