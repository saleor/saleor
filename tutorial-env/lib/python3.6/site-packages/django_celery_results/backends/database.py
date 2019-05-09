from __future__ import absolute_import, unicode_literals

from celery.backends.base import BaseDictBackend
from celery.utils.serialization import b64encode, b64decode

from ..models import TaskResult


class DatabaseBackend(BaseDictBackend):
    """The Django database backend, using models to store task state."""

    TaskModel = TaskResult

    subpolling_interval = 0.5

    def _store_result(self, task_id, result, status,
                      traceback=None, request=None):
        """Store return value and status of an executed task."""
        content_type, content_encoding, result = self.encode_content(result)
        _, _, meta = self.encode_content({
            'children': self.current_task_children(request),
        })

        task_name = getattr(request, 'task', None) if request else None
        task_args = getattr(request, 'args', None) if request else None
        task_kwargs = getattr(request, 'kwargs', None) if request else None

        self.TaskModel._default_manager.store_result(
            content_type, content_encoding,
            task_id, result, status,
            traceback=traceback,
            meta=meta,
            task_name=task_name,
            task_args=task_args,
            task_kwargs=task_kwargs,
        )
        return result

    def _get_task_meta_for(self, task_id):
        """Get task metadata for a task by id."""
        obj = self.TaskModel._default_manager.get_task(task_id)
        res = obj.as_dict()
        meta = self.decode_content(obj, res.pop('meta', None)) or {}
        res.update(meta,
                   result=self.decode_content(obj, res.get('result')))
        return self.meta_from_decoded(res)

    def encode_content(self, data):
        content_type, content_encoding, content = self._encode(data)
        if content_encoding == 'binary':
            content = b64encode(content)
        return content_type, content_encoding, content

    def decode_content(self, obj, content):
        if content:
            if obj.content_encoding == 'binary':
                content = b64decode(content)
            return self.decode(content)

    def _forget(self, task_id):
        try:
            self.TaskModel._default_manager.get(task_id=task_id).delete()
        except self.TaskModel.DoesNotExist:
            pass

    def cleanup(self):
        """Delete expired metadata."""
        self.TaskModel._default_manager.delete_expired(self.expires)
