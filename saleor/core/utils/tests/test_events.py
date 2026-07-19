from unittest import mock

from django.db import transaction

from ..events import call_event


@mock.patch.object(transaction, "get_connection", wraps=transaction.get_connection)
def test_call_event_triggers_provided_method(
    mocked_transaction,
    checkout_info,
    plugins_manager,
    django_capture_on_commit_callbacks,
):
    # given
    mocked_fun = mock.Mock()
    expected_args = [1, 2]
    expected_kwargs = {"one": True, "two": False}

    # when
    with django_capture_on_commit_callbacks(execute=True):
        call_event(mocked_fun, *expected_args, **expected_kwargs)

    # then
    assert mocked_transaction.called
    mocked_fun.assert_called_with(*expected_args, **expected_kwargs)
