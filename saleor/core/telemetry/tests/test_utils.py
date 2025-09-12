import json
from unittest.mock import ANY, MagicMock, patch

import pytest
from opentelemetry.attributes import BoundedAttributes
from opentelemetry.trace import INVALID_SPAN_CONTEXT, Link, SpanContext, TraceFlags
from opentelemetry.util.types import AttributeValue

from ..utils import (
    Scope,
    TelemetryTaskContext,
    Unit,
    convert_unit,
    enrich_span_with_global_attributes,
    enrich_with_global_attributes,
    get_global_attributes,
    set_global_attributes,
    task_with_telemetry_context,
)


def test_scope_is_service():
    assert Scope.SERVICE.is_service is True
    assert Scope.CORE.is_service is False


def test_convert_unit_same_unit():
    # Same unit should return the same value
    assert convert_unit(100, Unit.SECOND, Unit.SECOND) == 100
    assert convert_unit(100, Unit.MILLISECOND, Unit.MILLISECOND) == 100
    assert convert_unit(100, Unit.NANOSECOND, Unit.NANOSECOND) == 100


def test_convert_unit_supported_conversions():
    # Test nanoseconds to milliseconds
    assert convert_unit(1000000, Unit.NANOSECOND, Unit.MILLISECOND) == 1

    # Test nanoseconds to seconds
    assert convert_unit(1000000000, Unit.NANOSECOND, Unit.SECOND) == 1


@pytest.mark.parametrize(
    ("from_unit", "to_unit"),
    [
        (Unit.MILLISECOND, Unit.REQUEST),
        (None, Unit.REQUEST),
        (Unit.REQUEST, Unit.MILLISECOND),
    ],
)
def test_convert_unit_unsupported_conversion(from_unit, to_unit):
    with pytest.raises(ValueError, match="Conversion from .* to .* not supported"):
        convert_unit(100, from_unit, to_unit)


def test_convert_unit_unsupported_conversion_with_raising_disabled(settings):
    settings.TELEMETRY_RAISE_UNIT_CONVERSION_ERRORS = False

    # Test unsupported conversion (e.g., milliseconds to requests)
    with patch("saleor.core.telemetry.utils.logger.error") as mock_error:
        assert convert_unit(100, Unit.MILLISECOND, Unit.REQUEST) == 100
        mock_error.assert_called_once_with(
            "Conversion from Unit.MILLISECOND to Unit.REQUEST not supported",
            exc_info=ANY,
        )


def test_global_attributes():
    # Test setting and getting global attributes
    test_attrs: dict[str, AttributeValue] = {"test_key": "test_value"}

    # Initial global attributes should be empty
    assert get_global_attributes() == {}

    # Set global attributes
    with set_global_attributes(test_attrs):
        # Get global attributes
        assert get_global_attributes() == test_attrs

        # Nested attributes should work
        nested_attrs: dict[str, AttributeValue] = {"nested_key": "nested_value"}
        with set_global_attributes(nested_attrs):
            assert get_global_attributes() == nested_attrs

        # After exiting nested context, should return to original attributes
        assert get_global_attributes() == test_attrs

    # After exiting context, should be empty again
    assert get_global_attributes() == {}


def test_enrich_with_global_attributes():
    # given
    global_attrs: dict[str, AttributeValue] = {"global_key": "global_value"}
    local_attrs: dict[str, AttributeValue] = {"local_key": "local_value"}

    with set_global_attributes(global_attrs):
        # when
        enriched = enrich_with_global_attributes(local_attrs)

        # then
        assert enriched is not None
        assert "global_key" in enriched
        assert "local_key" in enriched
        assert enriched["global_key"] == "global_value"
        assert enriched["local_key"] == "local_value"


def test_enrich_with_global_attributes_none():
    # given
    global_attrs: dict[str, AttributeValue] = {"global_key": "global_value"}

    with set_global_attributes(global_attrs):
        # when
        enriched = enrich_with_global_attributes(None)

        # then
        assert enriched == global_attrs


def test_enrich_span_with_global_attributes():
    # given
    global_attrs: dict[str, AttributeValue] = {"global_key": "global_value"}
    local_attrs: dict[str, AttributeValue] = {"local_key": "local_value"}
    span_name = "graphql_query"

    with set_global_attributes(global_attrs):
        # when
        enriched = enrich_span_with_global_attributes(local_attrs, span_name)

        # then
        assert enriched is not None
        assert enriched["operation.name"] == span_name
        assert enriched["global_key"] == "global_value"
        assert enriched["local_key"] == "local_value"


def test_enrich_span_with_global_attributes_none():
    # given
    global_attrs: dict[str, AttributeValue] = {"global_key": "global_value"}
    span_name = "graphql_query"

    with set_global_attributes(global_attrs):
        # when
        enriched = enrich_span_with_global_attributes(None, span_name)

        # then
        assert enriched == {"operation.name": span_name, **global_attrs}


def test_telemetry_task_context_to_dict():
    # given
    span_context = SpanContext(
        trace_id=12345, span_id=67890, is_remote=True, trace_flags=TraceFlags(1)
    )
    link = Link(context=span_context, attributes={"link_attr": "link_value"})

    # when
    global_attrs: dict[str, AttributeValue] = {"global_key": "global_value"}
    context = TelemetryTaskContext(links=[link], global_attributes=global_attrs)

    # then
    data = context.to_dict()
    assert "links" in data
    assert "global_attributes" in data
    assert len(data["links"]) == 1
    assert "context" in data["links"][0]
    assert "attributes" in data["links"][0]
    assert data["links"][0]["context"]["trace_id"] == 12345
    assert data["links"][0]["context"]["span_id"] == 67890
    assert data["links"][0]["context"]["trace_flags"] == 1
    assert data["links"][0]["attributes"] == {"link_attr": "link_value"}
    assert data["global_attributes"] == global_attrs


def test_telemetry_task_context_to_dict_skip_link_to_invalid_span():
    # given
    global_attrs = {"global_key": "global_value"}
    link = Link(context=INVALID_SPAN_CONTEXT, attributes={"link_attr": "link_value"})

    # when
    context = TelemetryTaskContext(links=[link], global_attributes=global_attrs)

    # then
    assert context.to_dict() == {"global_attributes": global_attrs, "links": []}


def test_telemetry_task_context_to_dict_is_json_serializable():
    # given
    trace_id, span_id, trace_flags = 12345, 67890, 1
    span_attributes = {"link_attr": "link_value"}
    global_attrs = {"global_key": "global_value"}
    span_context = SpanContext(
        trace_id=trace_id,
        span_id=span_id,
        is_remote=True,
        trace_flags=TraceFlags(trace_flags),
    )
    link = Link(
        context=span_context, attributes=BoundedAttributes(attributes=span_attributes)
    )

    # when
    context = TelemetryTaskContext(links=[link], global_attributes=global_attrs)

    # then
    data = context.to_dict()
    assert data == {
        "global_attributes": global_attrs,
        "links": [
            {
                "context": {
                    "trace_id": 12345,
                    "span_id": 67890,
                    "trace_flags": 1,
                },
                "attributes": span_attributes,
            }
        ],
    }
    try:
        json.dumps(data)
    except Exception as e:
        pytest.fail(f"Failed to serialize telemetry context to JSON: {e}")


def test_telemetry_task_context_from_dict():
    # given
    data = {
        "links": [
            {
                "context": {
                    "trace_id": 12345,
                    "span_id": 67890,
                    "trace_flags": 1,
                },
                "attributes": {"link_attr": "link_value"},
            }
        ],
        "global_attributes": {"global_key": "global_value"},
    }

    # when
    context = TelemetryTaskContext.from_dict(data)

    # then
    assert context.links is not None
    assert len(context.links) == 1
    assert context.links[0].context.trace_id == 12345
    assert context.links[0].context.span_id == 67890
    assert context.links[0].context.trace_flags == TraceFlags(1)
    assert context.links[0].attributes == {"link_attr": "link_value"}
    assert context.global_attributes == {"global_key": "global_value"}


def test_telemetry_task_context_from_dict_invalid():
    invalid_data = {
        "links": [
            {
                "invalid_key": "invalid_value",
            }
        ],
    }

    # should raise ValueError
    with pytest.raises(ValueError, match="Invalid telemetry context data"):
        TelemetryTaskContext.from_dict(invalid_data)


def test_telemetry_task_context_from_dict_empty():
    # when
    context = TelemetryTaskContext.from_dict(None)

    # then
    assert context.links is None
    assert context.global_attributes == {}


def test_telemetry_task_context_from_dict_skip_link_to_invalid_span():
    data = {
        "links": [
            {
                "context": {
                    "trace_id": 0,
                    "span_id": 0,
                    "trace_flags": 0,
                },
                "attributes": {"link_attr": "link_value"},
            }
        ],
        "global_attributes": {"global_key": "global_value"},
    }

    # when
    context = TelemetryTaskContext.from_dict(data)

    # then
    assert context.global_attributes == {"global_key": "global_value"}
    assert context.links == []


@patch("saleor.core.telemetry.utils.set_global_attributes")
def test_task_with_telemetry_context_decorator(mock_set_global_attrs):
    # given
    mock_func = MagicMock()
    decorated_func = task_with_telemetry_context(mock_func)
    context = TelemetryTaskContext(global_attributes={"test": "value"})

    # when
    decorated_func(telemetry_context=context.to_dict())

    # then
    mock_set_global_attrs.assert_called_once_with({"test": "value"})
    mock_func.assert_called_once()
    assert "telemetry_context" in mock_func.call_args.kwargs
    assert isinstance(
        mock_func.call_args.kwargs["telemetry_context"], TelemetryTaskContext
    )


@patch("saleor.core.telemetry.utils.set_global_attributes")
@patch("saleor.core.telemetry.utils.logger.warning")
def test_task_with_telemetry_context_decorator_no_context(
    mock_warning, mock_set_global_attrs
):
    # given
    mock_func = MagicMock()
    decorated_func = task_with_telemetry_context(mock_func)

    # when
    decorated_func()

    # then
    mock_warning.assert_called_once_with("No telemetry_context provided for the task")
    mock_set_global_attrs.assert_called_once_with({})
    mock_func.assert_called_once()


@patch("saleor.core.telemetry.utils.set_global_attributes")
@patch("saleor.core.telemetry.utils.logger.exception")
def test_task_with_telemetry_context_decorator_invalid_links_context(
    mock_logger, mock_set_global_attrs
):
    # given
    mock_func = MagicMock()
    decorated_func = task_with_telemetry_context(mock_func)

    # when
    decorated_func(telemetry_context={"links": [{"invalid": "context"}]})

    # then
    mock_logger.assert_called_once_with("Failed to parse telemetry context")
    mock_set_global_attrs.assert_called_once_with({})
    mock_func.assert_called_once()


@patch("saleor.core.telemetry.utils.set_global_attributes")
def test_task_with_telemetry_context_decorator_invalid_context(mock_set_global_attrs):
    # given
    mock_func = MagicMock()
    decorated_func = task_with_telemetry_context(mock_func)

    # when
    decorated_func(telemetry_context={"invalid": "context"})

    # then
    mock_set_global_attrs.assert_called_once_with({})
    mock_func.assert_called_once()
