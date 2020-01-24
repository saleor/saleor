from ddtrace.opentracer import Tracer as DDTracer, set_global_tracer
from django.core.exceptions import ImproperlyConfigured
from jaeger_client import Config as JaegerConfig


class OpenTracingConfig:
    def __init__(self, *args, **kwargs):
        self.tracing_mapper = {
            "DATADOG": self._init_datadog_tracer,
            "JAEGER": self._init_jaeger_tracer,
        }

        try:
            int(kwargs.get("reporting_port"))
        except (TypeError, ValueError):
            self.raise_configuration_error()

        if kwargs.get("tracer_type") not in self.tracing_mapper or not kwargs.get(
            "reporting_host"
        ):
            self.raise_configuration_error()

        for prop in ["tracer_type", "reporting_host", "reporting_port"]:
            setattr(self, prop, kwargs[prop])

    @staticmethod
    def raise_configuration_error():
        raise ImproperlyConfigured(
            "When ENABLE_OPENTRACING is active, you need to set TRACER_TYPE, "
            "TRACER_REPORTING_HOST and TRACER_REPORTING_PORT."
        )

    def _get_tracer(self):
        return self.tracing_mapper[self.tracer_type]

    def create_global_tracer(self, service_name):
        return self._get_tracer()(service_name)

    def _init_datadog_tracer(self, service_name):
        config = {
            "agent_hostname": self.reporting_host,
            "agent_port": int(self.reporting_port),
        }
        tracer = DDTracer(service_name, config=config)
        # set the DD tracer as default for opentracing.
        set_global_tracer(tracer)
        return tracer

    def _init_jaeger_tracer(self, service_name):
        jaeger = JaegerConfig(
            config={
                "sampler": {"type": "const", "param": 1},
                "local_agent": {
                    "reporting_host": self.reporting_host,
                    "reporting_port": int(self.reporting_port),
                },
                "logging": True,
            },
            service_name=service_name,
            validate=True,
        )
        # initialize_tracer() also sets the Jaeger tracer as default for opentracing.
        return jaeger.initialize_tracer()
