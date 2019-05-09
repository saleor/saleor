# -*- coding: utf-8 -*-
"""Amazon SQS Connection."""
from __future__ import absolute_import, unicode_literals

from vine import transform

from kombu.asynchronous.aws.connection import AsyncAWSQueryConnection

from .ext import boto3
from .message import AsyncMessage
from .queue import AsyncQueue


__all__ = ('AsyncSQSConnection',)


class AsyncSQSConnection(AsyncAWSQueryConnection):
    """Async SQS Connection."""

    def __init__(self, sqs_connection, debug=0, region=None, **kwargs):
        if boto3 is None:
            raise ImportError('boto3 is not installed')
        AsyncAWSQueryConnection.__init__(
            self,
            sqs_connection,
            region_name=region, debug=debug,
            **kwargs
        )

    def create_queue(self, queue_name,
                     visibility_timeout=None, callback=None):
        params = {'QueueName': queue_name}
        if visibility_timeout:
            params['DefaultVisibilityTimeout'] = format(
                visibility_timeout, 'd',
            )
        return self.get_object('CreateQueue', params,
                               callback=callback)

    def delete_queue(self, queue, force_deletion=False, callback=None):
        return self.get_status('DeleteQueue', None, queue.id,
                               callback=callback)

    def get_queue_url(self, queue):
        res = self.sqs_connection.get_queue_url(QueueName=queue)
        return res['QueueUrl']

    def get_queue_attributes(self, queue, attribute='All', callback=None):
        return self.get_object(
            'GetQueueAttributes', {'AttributeName': attribute},
            queue.id, callback=callback,
        )

    def set_queue_attribute(self, queue, attribute, value, callback=None):
        return self.get_status(
            'SetQueueAttribute',
            {'Attribute.Name': attribute, 'Attribute.Value': value},
            queue.id, callback=callback,
        )

    def receive_message(self, queue,
                        number_messages=1, visibility_timeout=None,
                        attributes=None, wait_time_seconds=None,
                        callback=None):
        params = {'MaxNumberOfMessages': number_messages}
        if visibility_timeout:
            params['VisibilityTimeout'] = visibility_timeout
        if attributes:
            attrs = {}
            for idx, attr in enumerate(attributes):
                attrs['AttributeName.' + str(idx + 1)] = attr
            params.update(attrs)
        if wait_time_seconds is not None:
            params['WaitTimeSeconds'] = wait_time_seconds
        queue_url = self.get_queue_url(queue)
        return self.get_list(
            'ReceiveMessage', params, [('Message', AsyncMessage)],
            queue_url, callback=callback, parent=queue,
        )

    def delete_message(self, queue, receipt_handle, callback=None):
        return self.delete_message_from_handle(
            queue, receipt_handle, callback,
        )

    def delete_message_batch(self, queue, messages, callback=None):
        params = {}
        for i, m in enumerate(messages):
            prefix = 'DeleteMessageBatchRequestEntry.{0}'.format(i + 1)
            params.update({
                '{0}.Id'.format(prefix): m.id,
                '{0}.ReceiptHandle'.format(prefix): m.receipt_handle,
            })
        return self.get_object(
            'DeleteMessageBatch', params, queue.id,
            verb='POST', callback=callback,
        )

    def delete_message_from_handle(self, queue, receipt_handle,
                                   callback=None):
        return self.get_status(
            'DeleteMessage', {'ReceiptHandle': receipt_handle},
            queue, callback=callback,
        )

    def send_message(self, queue, message_content,
                     delay_seconds=None, callback=None):
        params = {'MessageBody': message_content}
        if delay_seconds:
            params['DelaySeconds'] = int(delay_seconds)
        return self.get_object(
            'SendMessage', params, queue.id,
            verb='POST', callback=callback,
        )

    def send_message_batch(self, queue, messages, callback=None):
        params = {}
        for i, msg in enumerate(messages):
            prefix = 'SendMessageBatchRequestEntry.{0}'.format(i + 1)
            params.update({
                '{0}.Id'.format(prefix): msg[0],
                '{0}.MessageBody'.format(prefix): msg[1],
                '{0}.DelaySeconds'.format(prefix): msg[2],
            })
        return self.get_object(
            'SendMessageBatch', params, queue.id,
            verb='POST', callback=callback,
        )

    def change_message_visibility(self, queue, receipt_handle,
                                  visibility_timeout, callback=None):
        return self.get_status(
            'ChangeMessageVisibility',
            {'ReceiptHandle': receipt_handle,
             'VisibilityTimeout': visibility_timeout},
            queue.id, callback=callback,
        )

    def change_message_visibility_batch(self, queue, messages, callback=None):
        params = {}
        for i, t in enumerate(messages):
            pre = 'ChangeMessageVisibilityBatchRequestEntry.{0}'.format(i + 1)
            params.update({
                '{0}.Id'.format(pre): t[0].id,
                '{0}.ReceiptHandle'.format(pre): t[0].receipt_handle,
                '{0}.VisibilityTimeout'.format(pre): t[1],
            })
        return self.get_object(
            'ChangeMessageVisibilityBatch', params, queue.id,
            verb='POST', callback=callback,
        )

    def get_all_queues(self, prefix='', callback=None):
        params = {}
        if prefix:
            params['QueueNamePrefix'] = prefix
        return self.get_list(
            'ListQueues', params, [('QueueUrl', AsyncQueue)],
            callback=callback,
        )

    def get_queue(self, queue_name, callback=None):
        # TODO Does not support owner_acct_id argument
        return self.get_all_queues(
            queue_name,
            transform(self._on_queue_ready, callback, queue_name),
        )
    lookup = get_queue

    def _on_queue_ready(self, name, queues):
        return next(
            (q for q in queues if q.url.endswith(name)), None,
        )

    def get_dead_letter_source_queues(self, queue, callback=None):
        return self.get_list(
            'ListDeadLetterSourceQueues', {'QueueUrl': queue.url},
            [('QueueUrl', AsyncQueue)],
            callback=callback,
        )

    def add_permission(self, queue, label, aws_account_id, action_name,
                       callback=None):
        return self.get_status(
            'AddPermission',
            {'Label': label,
             'AWSAccountId': aws_account_id,
             'ActionName': action_name},
            queue.id, callback=callback,
        )

    def remove_permission(self, queue, label, callback=None):
        return self.get_status(
            'RemovePermission', {'Label': label}, queue.id, callback=callback,
        )
