# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals


def connect_sqs(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
    """Return async connection to Amazon SQS."""
    from .sqs.connection import AsyncSQSConnection
    return AsyncSQSConnection(
        aws_access_key_id, aws_secret_access_key, **kwargs
    )
