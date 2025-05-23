import json
import math
from decimal import Decimal

import pytest
from django.conf import settings
from django.db import connections
from opentelemetry.sdk.metrics.export import DataPointT, Metric, MetricsData
from opentelemetry.sdk.trace import ReadableSpan

from ..core.db.connection import allow_writer


class FakeDbReplicaConnection:
    """A class used to create a fake replica DB connection for use in tests.

    This class serves as a wrapper around the writer DB connection (alias "default")
    that simulates a replica DB connection by identifying itself with a replica alias
    and overriding cursor creation methods. It effectively results in one DB connection
    identified by two separate aliases, but with shared transactions.
    """

    def __init__(self, replica_conn):
        self.replica_conn = replica_conn
        self.writer_conn = connections[settings.DATABASE_CONNECTION_DEFAULT_NAME]

    def cursor(self, *args, **kwargs):
        with allow_writer():
            # Cursor creation is wrapped in allow_writer as it is effectively created
            # using the writer DB connection
            cursor = self.writer_conn.cursor(*args, **kwargs)
            cursor.db = self
        return cursor

    def chunked_cursor(self, *args, **kwargs):
        with allow_writer():
            # Cursor creation is wrapped in allow_writer as it is effectively created
            # using the writer DB connection
            cursor = self.writer_conn.chunked_cursor(*args, **kwargs)
            cursor.db = self
        return cursor

    def __getattr__(self, attr):
        if attr == "alias":
            return getattr(self.replica_conn, attr)
        return getattr(self.writer_conn, attr)


def prepare_test_db_connections():
    """Override the replica DB connection with a fake one for testing purposes.

    This function allows simulation of replica DB usage in tests while using Django's
    TestCase, avoiding the need for the slower TransactionTestCase. For more details,
    refer to the Django documentation:
    https://docs.djangoproject.com/en/4.2/topics/testing/advanced/#testing-primary-replica-configurations
    """
    replica = settings.DATABASE_CONNECTION_REPLICA_NAME
    connections[replica] = FakeDbReplicaConnection(connections[replica])  # type: ignore[assignment]


def dummy_editorjs(text, json_format=False):
    data = {"blocks": [{"data": {"text": text}, "type": "paragraph"}]}
    return json.dumps(data) if json_format else data


def round_down(price: Decimal) -> Decimal:
    return Decimal(math.floor(price * 100)) / 100


def round_up(price: Decimal) -> Decimal:
    return Decimal(math.ceil(price * 100)) / 100


def get_metric_data(metrics_data: MetricsData, metric_name: str) -> Metric:
    for resource in metrics_data.resource_metrics:
        for scope_metrics in resource.scope_metrics:
            for metric in scope_metrics.metrics:
                if metric.name == metric_name:
                    return metric
    raise KeyError(f"Metric {metric_name} not found in metrics data")


def get_metric_data_point(metrics_data: MetricsData, metric_name: str) -> DataPointT:
    metric_data = get_metric_data(metrics_data, metric_name)
    datapoints_count = len(metric_data.data.data_points)
    assert datapoints_count == 1, (
        f"For metric {metric_name} found {datapoints_count} instead of 1"
    )
    return metric_data.data.data_points[0]


def filter_spans_by_name(
    spans: tuple[ReadableSpan, ...], name
) -> tuple[ReadableSpan, ...]:
    return tuple(span for span in spans if span.name == name)


def get_span_by_name(spans: tuple[ReadableSpan, ...], name: str) -> ReadableSpan:
    __tracebackhide__ = True
    spans = filter_spans_by_name(spans, name)
    if not spans:
        pytest.fail(f"No span with name '{name}' found")
    if len(spans) > 1:
        pytest.fail(f"Multiple '{name}' spans")
    return spans[0]
