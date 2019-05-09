__all__ = [
    'split',
    'mkNonce',
    'checkTimestamp',
]

from openid import cryptutil
from time import strptime, strftime, gmtime, time
from calendar import timegm
import string

NONCE_CHARS = string.ascii_letters + string.digits

# Keep nonces for five hours (allow five hours for the combination of
# request time and clock skew). This is probably way more than is
# necessary, but there is not much overhead in storing nonces.
SKEW = 60 * 60 * 5

time_fmt = '%Y-%m-%dT%H:%M:%SZ'
time_str_len = len('0000-00-00T00:00:00Z')


def split(nonce_string):
    """Extract a timestamp from the given nonce string

    @param nonce_string: the nonce from which to extract the timestamp
    @type nonce_string: str

    @returns: A pair of a Unix timestamp and the salt characters
    @returntype: (int, str)

    @raises ValueError: if the nonce does not start with a correctly
        formatted time string
    """
    timestamp_str = nonce_string[:time_str_len]
    try:
        timestamp = timegm(strptime(timestamp_str, time_fmt))
    except AssertionError:  # Python 2.2
        timestamp = -1
    if timestamp < 0:
        raise ValueError('time out of range')
    return timestamp, nonce_string[time_str_len:]


def checkTimestamp(nonce_string, allowed_skew=SKEW, now=None):
    """Is the timestamp that is part of the specified nonce string
    within the allowed clock-skew of the current time?

    @param nonce_string: The nonce that is being checked
    @type nonce_string: str

    @param allowed_skew: How many seconds should be allowed for
        completing the request, allowing for clock skew.
    @type allowed_skew: int

    @param now: The current time, as a Unix timestamp
    @type now: int

    @returntype: bool
    @returns: Whether the timestamp is correctly formatted and within
        the allowed skew of the current time.
    """
    try:
        stamp, _ = split(nonce_string)
    except ValueError:
        return False
    else:
        if now is None:
            now = time()

        # Time after which we should not use the nonce
        past = now - allowed_skew

        # Time that is too far in the future for us to allow
        future = now + allowed_skew

        # the stamp is not too far in the future and is not too far in
        # the past
        return past <= stamp <= future


def mkNonce(when=None):
    """Generate a nonce with the current timestamp

    @param when: Unix timestamp representing the issue time of the
        nonce. Defaults to the current time.
    @type when: int

    @returntype: str
    @returns: A string that should be usable as a one-way nonce

    @see: time
    """
    salt = cryptutil.randomString(6, NONCE_CHARS)
    if when is None:
        t = gmtime()
    else:
        t = gmtime(when)

    time_str = strftime(time_fmt, t)
    return time_str + salt
