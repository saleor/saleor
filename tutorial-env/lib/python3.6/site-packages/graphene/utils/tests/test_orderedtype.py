from ..orderedtype import OrderedType


def test_orderedtype():
    one = OrderedType()
    two = OrderedType()
    three = OrderedType()

    assert one < two < three


def test_orderedtype_eq():
    one = OrderedType()
    two = OrderedType()

    assert one == one
    assert one != two


def test_orderedtype_hash():
    one = OrderedType()
    two = OrderedType()

    assert hash(one) == hash(one)
    assert hash(one) != hash(two)


def test_orderedtype_resetcounter():
    one = OrderedType()
    two = OrderedType()
    one.reset_counter()

    assert one > two


def test_orderedtype_non_orderabletypes():
    one = OrderedType()

    assert one.__lt__(1) == NotImplemented
    assert one.__gt__(1) == NotImplemented
    assert not one == 1
