from opentelemetry import trace

# Create a global tracer instance
tracer = trace.get_tracer("saleor.tracer")
