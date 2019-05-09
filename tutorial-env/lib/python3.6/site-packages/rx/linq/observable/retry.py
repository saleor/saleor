from rx.core import Observable
from rx.internal.enumerable import Enumerable
from rx.internal import extensionmethod


@extensionmethod(Observable)
def retry(self, retry_count=None):
    """Repeats the source observable sequence the specified number of times
    or until it successfully terminates. If the retry count is not
    specified, it retries indefinitely.

    1 - retried = retry.repeat()
    2 - retried = retry.repeat(42)

    retry_count -- [Optional] Number of times to retry the sequence. If not
    provided, retry the sequence indefinitely.

    Returns an observable sequence producing the elements of the given
    sequence repeatedly until it terminates successfully.
    """

    return Observable.catch_exception(Enumerable.repeat(self, retry_count))
