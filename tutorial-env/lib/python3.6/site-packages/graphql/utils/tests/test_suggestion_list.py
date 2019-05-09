from graphql.utils.suggestion_list import suggestion_list


def test_returns_results_when_input_is_empty():
    assert suggestion_list("", ["a"]) == ["a"]


def test_returns_empty_array_when_there_are_no_options():
    assert suggestion_list("input", []) == []


def test_returns_options_sorted_based_on_similarity():
    assert suggestion_list("abc", ["a", "ab", "abc"]) == ["abc", "ab"]

    assert suggestion_list("csutomer", ["customer", "stomer", "store"]) == [
        "customer",
        "stomer",
        "store",
    ]
