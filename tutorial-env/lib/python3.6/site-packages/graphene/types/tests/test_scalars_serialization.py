from ..scalars import Boolean, Float, Int, String


def test_serializes_output_int():
    assert Int.serialize(1) == 1
    assert Int.serialize(0) == 0
    assert Int.serialize(-1) == -1
    assert Int.serialize(0.1) == 0
    assert Int.serialize(1.1) == 1
    assert Int.serialize(-1.1) == -1
    assert Int.serialize(1e5) == 100000
    assert Int.serialize(9876504321) is None
    assert Int.serialize(-9876504321) is None
    assert Int.serialize(1e100) is None
    assert Int.serialize(-1e100) is None
    assert Int.serialize("-1.1") == -1
    assert Int.serialize("one") is None
    assert Int.serialize(False) == 0
    assert Int.serialize(True) == 1


def test_serializes_output_float():
    assert Float.serialize(1) == 1.0
    assert Float.serialize(0) == 0.0
    assert Float.serialize(-1) == -1.0
    assert Float.serialize(0.1) == 0.1
    assert Float.serialize(1.1) == 1.1
    assert Float.serialize(-1.1) == -1.1
    assert Float.serialize("-1.1") == -1.1
    assert Float.serialize("one") is None
    assert Float.serialize(False) == 0
    assert Float.serialize(True) == 1


def test_serializes_output_string():
    assert String.serialize("string") == "string"
    assert String.serialize(1) == "1"
    assert String.serialize(-1.1) == "-1.1"
    assert String.serialize(True) == "true"
    assert String.serialize(False) == "false"
    assert String.serialize(u"\U0001F601") == u"\U0001F601"


def test_serializes_output_boolean():
    assert Boolean.serialize("string") is True
    assert Boolean.serialize("") is False
    assert Boolean.serialize(1) is True
    assert Boolean.serialize(0) is False
    assert Boolean.serialize(True) is True
    assert Boolean.serialize(False) is False
