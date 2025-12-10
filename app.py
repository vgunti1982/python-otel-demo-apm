import os
import time
import random
from flask import Flask, request
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

# Setup Resource
resource = Resource.create({
    "service.name": "python-demo-app",
    "service.version": "1.0.0"
})

# Setup OTLP Exporter
otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

trace_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
trace_provider = TracerProvider(resource=resource)
trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
trace.set_tracer_provider(trace_provider)

metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint)
metric_reader = PeriodicExportingMetricReader(metric_exporter)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)

# Initialize Flask app
app = Flask(__name__)

# Auto-instrument Flask and Requests
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# Get tracer
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Create metrics
request_counter = meter.create_counter(
    "app.requests.total",
    description="Total number of requests"
)

request_duration = meter.create_histogram(
    "app.request.duration",
    unit="ms",
    description="Request duration in milliseconds"
)

@app.route("/")
def index():
    return {
        "message": "Hello from OTEL Demo App!",
        "endpoints": [
            "/api/users",
            "/api/process",
            "/health"
        ]
    }

@app.route("/api/users")
def get_users():
    with tracer.start_as_current_span("fetch_users") as span:
        span.set_attribute("db.system", "postgresql")
        span.set_attribute("db.operation", "select")
        
        # Simulate database query
        time.sleep(random.uniform(0.1, 0.3))
        
        users = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"}
        ]
        
        span.set_attribute("result.count", len(users))
        request_counter.add(1, {"endpoint": "/api/users"})
        
        return {"users": users}

@app.route("/api/process")
def process():
    start_time = time.time()
    
    with tracer.start_as_current_span("process_request") as parent_span:
        parent_span.set_attribute("operation", "multi_step_process")
        
        # Step 1: Validate
        with tracer.start_as_current_span("validate_data") as span:
            span.set_attribute("step", "validation")
            time.sleep(random.uniform(0.05, 0.15))
        
        # Step 2: Process
        with tracer.start_as_current_span("process_data") as span:
            span.set_attribute("step", "processing")
            time.sleep(random.uniform(0.1, 0.3))
        
        # Step 3: Save
        with tracer.start_as_current_span("save_results") as span:
            span.set_attribute("step", "saving")
            time.sleep(random.uniform(0.05, 0.2))
            span.set_attribute("records_saved", 42)
        
        duration = (time.time() - start_time) * 1000
        request_duration.record(duration, {"endpoint": "/api/process"})
        request_counter.add(1, {"endpoint": "/api/process"})
    
    return {"status": "success", "duration_ms": round(duration, 2)}

@app.route("/api/error")
def error_endpoint():
    with tracer.start_as_current_span("error_operation") as span:
        try:
            raise ValueError("Simulated error for tracing")
        except Exception as e:
            span.record_exception(e)
            span.set_attribute("error", True)
            request_counter.add(1, {"endpoint": "/api/error", "status": "error"})
            return {"error": str(e)}, 500

@app.route("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
