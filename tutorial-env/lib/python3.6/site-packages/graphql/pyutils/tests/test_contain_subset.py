from ..contain_subset import contain_subset

plain_object = {"a": "b", "c": "d"}

complex_object = {"a": "b", "c": "d", "e": {"foo": "bar", "baz": {"qux": "quux"}}}


def test_plain_object_should_pass_for_smaller_object():
    # type: () -> None
    assert contain_subset({"a": "b"}, plain_object)


def test_plain_object_should_pass_for_same_object():
    # type: () -> None
    assert contain_subset({"a": "b", "c": "d"}, plain_object)


def test_plain_object_should_reject_for_similar_object():
    # type: () -> None
    assert not contain_subset({"a": "notB", "c": "d"}, plain_object)


def test_complex_object_should_pass_for_smaller_object():
    # type: () -> None
    assert contain_subset({"a": "b", "e": {"foo": "bar"}}, complex_object)


def test_complex_object_should_pass_for_smaller_object_other():
    # type: () -> None
    assert contain_subset({"e": {"foo": "bar", "baz": {"qux": "quux"}}}, complex_object)


def test_complex_object_should_pass_for_same_object():
    # type: () -> None
    assert contain_subset(
        {"a": "b", "c": "d", "e": {"foo": "bar", "baz": {"qux": "quux"}}},
        complex_object,
    )


def test_complex_object_should_reject_for_similar_object():
    # type: () -> None
    assert not contain_subset(
        {"e": {"foo": "bar", "baz": {"qux": "notAQuux"}}}, complex_object
    )


# def test_circular_objects_should_contain_subdocument():
#     obj = {}
#     obj["arr"] = [obj, obj]
#     obj["arr"].append(obj["arr"])
#     obj["obj"] = obj

#     assert contain_subset(
#         {"arr": [{"arr": []}, {"arr": []}, [{"arr": []}, {"arr": []}]]}, obj
#     )


# def test_circular_objects_should_not_contain_similardocument():
#     obj = {}
#     obj["arr"] = [obj, obj]
#     obj["arr"].append(obj["arr"])
#     obj["obj"] = obj

#     assert not contain_subset(
#         {
#             "arr": [
#                 {"arr": ["just random field"]},
#                 {"arr": []},
#                 [{"arr": []}, {"arr": []}],
#             ]
#         },
#         obj,
#     )


def test_should_contain_others():
    obj = {"elems": [{"a": "b", "c": "d", "e": "f"}, {"g": "h"}]}
    assert contain_subset({"elems": [{"g": "h"}, {"a": "b", "e": "f"}]}, obj)
