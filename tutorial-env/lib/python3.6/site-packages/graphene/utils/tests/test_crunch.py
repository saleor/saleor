import pytest
from collections import OrderedDict

from ..crunch import crunch


@pytest.mark.parametrize(
    "description,uncrunched,crunched",
    [
        ["number primitive", 0, [0]],
        ["boolean primitive", True, [True]],
        ["string primitive", "string", ["string"]],
        ["empty array", [], [[]]],
        ["single-item array", [None], [None, [0]]],
        [
            "multi-primitive all distinct array",
            [None, 0, True, "string"],
            [None, 0, True, "string", [0, 1, 2, 3]],
        ],
        [
            "multi-primitive repeated array",
            [True, True, True, True],
            [True, [0, 0, 0, 0]],
        ],
        ["one-level nested array", [[1, 2, 3]], [1, 2, 3, [0, 1, 2], [3]]],
        ["two-level nested array", [[[1, 2, 3]]], [1, 2, 3, [0, 1, 2], [3], [4]]],
        ["empty object", {}, [{}]],
        ["single-item object", {"a": None}, [None, {"a": 0}]],
        [
            "multi-item all distinct object",
            OrderedDict([("a", None), ("b", 0), ("c", True), ("d", "string")]),
            [None, 0, True, "string", {"a": 0, "b": 1, "c": 2, "d": 3}],
        ],
        [
            "multi-item repeated object",
            OrderedDict([("a", True), ("b", True), ("c", True), ("d", True)]),
            [True, {"a": 0, "b": 0, "c": 0, "d": 0}],
        ],
        [
            "complex array",
            [OrderedDict([("a", True), ("b", [1, 2, 3])]), [1, 2, 3]],
            [True, 1, 2, 3, [1, 2, 3], {"a": 0, "b": 4}, [5, 4]],
        ],
        [
            "complex object",
            OrderedDict(
                [
                    ("a", True),
                    ("b", [1, 2, 3]),
                    ("c", OrderedDict([("a", True), ("b", [1, 2, 3])])),
                ]
            ),
            [True, 1, 2, 3, [1, 2, 3], {"a": 0, "b": 4}, {"a": 0, "b": 4, "c": 5}],
        ],
    ],
)
def test_crunch(description, uncrunched, crunched):
    assert crunch(uncrunched) == crunched
