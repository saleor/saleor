from rx.internal.basic import default_comparer

def create_message(actual, expected):
    return '\r\n\tExpected: [%s]\r\n\tActual:   [%s]' % (str(expected), str(actual))

def are_elements_equal(expected, actual, comparer=None, message=None):
    is_ok = True
    comparer = comparer or default_comparer
    if len(expected) != len(actual):
        msg = 'Not equal length. Expected: %s Actual: %s' % (len(expected), len(actual))
        assert False, msg
        return

    for i, ex in enumerate(expected):
        is_ok = comparer(ex, actual[i])
        if not is_ok:
            break

    assert is_ok, message or create_message(actual, expected)

def assert_equal(expected, *actual):
    actual = list(actual)
    return are_elements_equal(expected, actual, default_comparer)

class AssertList(list):
    def assert_equal(self, *expected):
        expected = list(expected)
        return are_elements_equal(expected, self, default_comparer)
