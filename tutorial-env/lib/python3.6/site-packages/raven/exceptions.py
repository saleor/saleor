from __future__ import absolute_import

from raven.utils.compat import text_type


class APIError(Exception):
    def __init__(self, message, code=0):
        self.code = code
        self.message = message

    def __unicode__(self):
        return text_type("%s: %s" % (self.message, self.code))


class RateLimited(APIError):
    def __init__(self, message, retry_after=0):
        self.retry_after = retry_after
        super(RateLimited, self).__init__(message, 429)


class InvalidGitRepository(Exception):
    pass


class ConfigurationError(ValueError):
    pass


class InvalidDsn(ConfigurationError):
    pass
