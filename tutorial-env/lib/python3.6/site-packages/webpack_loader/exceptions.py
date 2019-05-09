__all__ = (
    'WebpackError',
    'WebpackLoaderBadStatsError',
    'WebpackLoaderTimeoutError',
    'WebpackBundleLookupError'
)


class BaseWebpackLoaderException(Exception):
    """
    Base exception for django-webpack-loader.
    """


class WebpackError(BaseWebpackLoaderException):
    """
    General webpack loader error.
    """


class WebpackLoaderBadStatsError(BaseWebpackLoaderException):
    """
    The stats file does not contain valid data.
    """


class WebpackLoaderTimeoutError(BaseWebpackLoaderException):
    """
    The bundle took too long to compile.
    """


class WebpackBundleLookupError(BaseWebpackLoaderException):
    """
    The bundle name was invalid.
    """
