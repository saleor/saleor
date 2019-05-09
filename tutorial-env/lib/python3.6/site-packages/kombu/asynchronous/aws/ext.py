# -*- coding: utf-8 -*-
"""Amazon boto3 interface."""
from __future__ import absolute_import, unicode_literals

try:
    import boto3
    from botocore import exceptions
    from botocore.awsrequest import AWSRequest
    from botocore.response import get_response
except ImportError:
    boto3 = None

    class _void(object):
        pass

    class BotoCoreError(Exception):
        pass
    exceptions = _void()
    exceptions.BotoCoreError = BotoCoreError
    AWSRequest = _void()
    get_response = _void()


__all__ = (
    'exceptions', 'AWSRequest', 'get_response'
)
