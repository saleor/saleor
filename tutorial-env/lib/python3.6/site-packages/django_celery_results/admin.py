"""Result Task Admin interface."""
from __future__ import absolute_import, unicode_literals

from django.contrib import admin

from django.conf import settings
try:
    ALLOW_EDITS = settings.DJANGO_CELERY_RESULTS['ALLOW_EDITS']
except (AttributeError, KeyError) as e:
    ALLOW_EDITS = True
    pass

from .models import TaskResult


class TaskResultAdmin(admin.ModelAdmin):
    """Admin-interface for results of tasks."""

    model = TaskResult
    date_hierarchy = 'date_done'
    list_display = ('task_id', 'task_name', 'date_done', 'status')
    list_filter = ('status', 'date_done', 'task_name',)
    readonly_fields = ('date_done', 'result', 'hidden', 'meta')
    search_fields = ('task_name', 'task_id', 'status')
    fieldsets = (
        (None, {
            'fields': (
                'task_id',
                'task_name',
                'status',
                'content_type',
                'content_encoding',
            ),
            'classes': ('extrapretty', 'wide')
        }),
        ('Parameters', {
            'fields': (
                'task_args',
                'task_kwargs',
            ),
            'classes': ('extrapretty', 'wide')
        }),
        ('Result', {
            'fields': (
                'result',
                'date_done',
                'traceback',
                'hidden',
                'meta',
            ),
            'classes': ('extrapretty', 'wide')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if ALLOW_EDITS:
            return self.readonly_fields
        else:
            return list(set(
                [field.name for field in self.opts.local_fields]
            ))


admin.site.register(TaskResult, TaskResultAdmin)
