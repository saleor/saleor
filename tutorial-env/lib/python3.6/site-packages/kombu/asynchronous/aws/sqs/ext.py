# -*- coding: utf-8 -*-
"""Amazon SQS boto3 interface."""

from __future__ import absolute_import, unicode_literals

try:
    import boto3
except ImportError:
    boto3 = None
