# Python OpenTelemetry APM with Jaeger - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [app.py Documentation](#apppy-documentation)
4. [test_app.py Documentation](#test_apppy-documentation)
5. [Dockerfile Documentation](#dockerfile-documentation)
6. [docker-compose.yml Documentation](#docker-composeyml-documentation)
7. [Setup Instructions](#setup-instructions)
8. [API Endpoints](#api-endpoints)
9. [Monitoring and Debugging](#monitoring-and-debugging)

---

## Overview

This project demonstrates a complete Python Flask application with OpenTelemetry (OTEL) instrumentation that sends distributed traces to Jaeger. All components run in Docker containers, making it easy to deploy and test APM (Application Performance Monitoring) capabilities.

**Key Technologies:**
- Python 3.11 with Flask
- OpenTelemetry SDK for instrumentation
- OTLP (OpenTelemetry Protocol) gRPC exporter
- Jaeger for trace collection and visualization
- Docker & Docker Compose for containerization

---

## Architecture

```
┌─────────────────────┐
│   Flask App (OTEL)  │
│   - Instrumented    │
│   - Metrics         │
│   - Traces          │
└──────────┬──────────┘
           │
           ↓ (OTLP gRPC)
┌─────────────────────┐
│  OpenTelemetry SDK  │
│  - Span Processor   │
│  - Metric Reader    │
│  - Resource Setup   │
└──────────┬──────────┘
           │
           ↓ (OTLP gRPC Protocol)
┌─────────────────────┐
│  Jaeger Collector   │
│  - Span Receiver    │
│  - Storage          │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│   Jaeger UI/API     │
│  Port: 16686        │
└─────────────────────┘
```

---

## app.py Documentation

### Purpose
Main Flask application with full OpenTelemetry instrumentation. Demonstrates various tracing patterns including manual spans, nested operations, metrics, and error handling.

### Key Sections

#### Imports
```python
from flask import Flask
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
```
- **Flask**: Web framework
- **opentelemetry.trace**: Distributed tracing API
- **opentelemetry.metrics**: Metrics collection API
- **OTLPSpanExporter**: Sends spans to Jaeger via gRPC

#### Resource Configuration
```python
resource = Resource.create({
    "service.name": "python-demo-app",
    "service.version": "1.0.0"
})
```
- Identifies the service in Jaeger
- "service.name" is used to filter traces in Jaeger UI
- Metadata helps correlate traces from multiple services

#### Tracer Provider Setup
```python
trace_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
trace_provider = TracerProvider(resource=resource)
trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
trace.set_tracer_provider(trace_provider)
```
- **OTLPSpanExporter**: Exports spans to Jaeger (endpoint from env var)
- **BatchSpanProcessor**: Batches spans before sending (better performance)
- **set_tracer_provider**: Makes this the global tracer provider

#### Metrics Provider Setup
```python
metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint)
metric_reader = PeriodicExportingMetricReader(metric_exporter)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)
```
- Sets up metrics collection
- Periodically exports metrics to Jaeger
- Tracks request counts and durations

#### Auto-Instrumentation
```python
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()
```
- **FlaskInstrumentor**: Automatically creates spans for HTTP requests/responses
- **RequestsInstrumentor**: Automatically traces outgoing HTTP requests

#### Metrics Definition
```python
request_counter = meter.create_counter(
    "app.requests.total",
    description="Total number of requests"
)

request_duration = meter.create_histogram(
    "app.request.duration",
    unit="ms",
    description="Request duration in milliseconds"
)
```
- Counter: Increments with each request
- Histogram: Records request duration distribution

### Endpoints

#### GET `/`
Returns service information and available endpoints.
- No spans created (auto-instrumented by Flask)
- Useful for health checks

#### GET `/api/users`
Simulates a database query operation.
```python
with tracer.start_as_current_span("fetch_users") as span:
    span.set_attribute("db.system", "postgresql")
    span.set_attribute("db.operation", "select")
    time.sleep(random.uniform(0.1, 0.3))  # Simulates DB latency
```
- Manual span: "fetch_users"
- Span attributes: db.system, db.operation, result.count
- Increments request counter
- Shows in Jaeger with database metadata

#### GET `/api/process`
Multi-step process with nested spans.
```python
with tracer.start_as_current_span("process_request") as parent_span:
    # Step 1: Validate
    with tracer.start_as_current_span("validate_data"):
        time.sleep(...)
    
    # Step 2: Process
    with tracer.start_as_current_span("process_data"):
        time.sleep(...)
    
    # Step 3: Save
    with tracer.start_as_current_span("save_results"):
        time.sleep(...)
```
- Parent span: "process_request"
- Child spans: validate_data, process_data, save_results
- Shows hierarchical relationships in Jaeger
- Demonstrates nested context propagation

#### GET `/api/error`
Demonstrates error handling and exception recording.
```python
try:
    raise ValueError("Simulated error for tracing")
except Exception as e:
    span.record_exception(e)
    span.set_attribute("error", True)
```
- Records exceptions in spans
- Sets error flag for easy filtering
- Useful for debugging production issues

#### GET `/health`
Simple health check endpoint.
- Used by Docker health checks
- Quick way to verify app is running

### Environment Variables
- `OTEL_EXPORTER_OTLP_ENDPOINT`: Jaeger collector endpoint (default: `http://localhost:4317`)

### Key Tracing Concepts Used

**1. Spans**: Individual operations in a request
- Each `with tracer.start_as_current_span()` creates a span
- Spans have a start time, end time, and duration

**2. Span Context**: Automatically propagated through the call chain
- Child spans inherit parent context
- Jaeger uses this to build the trace tree

**3. Span Attributes**: Key-value metadata
- `span.set_attribute("key", "value")`
- Helps filter and analyze traces

**4. Exceptions**: Recorded in spans
- `span.record_exception(exception)`
- Visible in Jaeger for error analysis

**5. Metrics**: Time-series data
- Counters: cumulative values
- Histograms: value distributions

---

## test_app.py Documentation

### Purpose
Load testing and functional testing script that generates traces to verify the OTEL setup is working correctly.

### Key Sections

#### Base Configuration
```python
# The script uses an environment override so runners can target other hosts
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
```
- Points to the Flask app. When running the runner in Docker the recommended value is `http://python-app:8000` (Docker service DNS).
- You can override `BASE_URL` using an environment variable when running the script or via `docker-compose`.

#### Test Functions

**test_index()**
```python
def test_index():
    resp = requests.get(f"{BASE_URL}/")
    return resp.json()
```
- Tests the index endpoint
- Verifies app is running
- Creates a basic HTTP span

**test_users()**
```python
def test_users():
    resp = requests.get(f"{BASE_URL}/api/users")
    return resp.json()
```
- Tests database simulation endpoint
- Verifies nested spans are created
- Shows user data returned

**test_process()**
```python
def test_process():
    resp = requests.get(f"{BASE_URL}/api/process")
    return resp.json()
```
- Tests multi-step process endpoint
- Creates deepest span hierarchy
- Validates nested context propagation

**test_error()**
```python
def test_error():
    try:
        resp = requests.get(f"{BASE_URL}/api/error")
    except Exception as e:
        print(f"Error: {e}")
```
- Tests error handling
- Verifies exception recording works
- Shows error traces in Jaeger

**test_health()**
```python
def test_health():
    resp = requests.get(f"{BASE_URL}/health")
    return resp.json()
```
- Quick health check
- Verifies app connectivity

#### Load Testing Function
```python
def load_test(num_requests=20):
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request) for _ in range(num_requests)]
```
- Generates multiple concurrent requests
- Uses thread pool for parallelism
- Creates rich trace data for analysis
- Default: 20 requests with 5 concurrent workers

#### Main Execution Flow
```python
def main():
    try:
        test_health()
    except Exception as e:
        print(f"Error: App is not responding at {BASE_URL}")
```
- First checks if app is running
- Runs functional tests
- Runs load tests
- Provides clear feedback and Jaeger link

### Usage

**Run locally:**
```bash
python test_app.py
```

**Run in Docker:**
```bash
docker run -it --network claude_code_otel-network python:3.11-slim bash
pip install requests
python test_app.py
```

### Output Example
```
============================================================
OTEL Demo App - Test Suite
============================================================
[*] Testing GET /health
    Status: 200

[*] Running functional tests...
[*] Testing GET /
    Status: 200

[*] Testing GET /api/users
    Status: 200, Users: 3

[*] Testing GET /api/process
    Status: 200, Duration: 456.23ms

[*] Running load tests...
[*] Generating 30 requests for load testing...
[*] Load test completed

============================================================
[✓] Tests completed!
[*] View traces at: http://localhost:16686
============================================================
```

---

## Dockerfile Documentation

### Base Image
```dockerfile
FROM python:3.11-slim
```
- **python:3.11-slim**: Official Python image, minimal size (~150MB)
- Includes Python 3.11 and pip
- "slim" variant excludes non-essential packages

### Working Directory
```dockerfile
WORKDIR /app
```
- Sets working directory inside container
- All subsequent commands run in /app

### Dependency Installation
```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```
- **COPY requirements.txt**: Copies dependency list from host to container
- **pip install --no-cache-dir**: Installs packages without caching (reduces image size)
- Separated from app code for better Docker layer caching

### Application Copy
```dockerfile
COPY app.py .
```
- Copies the Flask application into container
- Placed after dependencies so code changes don't trigger re-installation

### Port Exposure
```dockerfile
EXPOSE 8000
```
- Documents that the container listens on port 8000
- Doesn't actually map the port (done in docker-compose.yml)

### Health Check
```dockerfile
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```
- Checks if app is healthy every 10 seconds
- Requires 3 failures to mark unhealthy
- Waits 5 seconds before first check (app startup time)
- Docker can restart unhealthy containers

### Startup Command
```dockerfile
CMD ["python", "app.py"]
```
- Runs the Flask app when container starts
- Python runs in unbuffered mode (good for logging)


### Build Optimization
- Multi-layer structure optimizes cache usage
- Requirements installed before app code
- Code changes only rebuild final layers
- Slim image reduces download size and security surface

---

## Test Runner

A lightweight containerized test runner was added to allow generating traces on demand. It includes:

- `Dockerfile.runner` — image for the runner based on `python:3.11-slim` that installs `requirements.txt` and copies the test script.
- `run_test_loop.sh` — the entrypoint script for the runner; by default it runs `python test_app.py` once and exits. This allows running traces only when desired.

Compose integration:

- Service name: `test_runner` in `docker-compose.yml`.
- Environment: `BASE_URL` is set to `http://python-app:8000` in the compose file so the runner targets the `python-app` service on the same network.
- The runner is intended to be run on-demand (it exits after a single run). To run the runner use the commands below.

Usage examples:

```bash
# Build the runner image
docker-compose build test_runner

# Run once and remove the container after exit
docker-compose run --rm test_runner

# Or start the service (it will run once and exit)
docker-compose up --build -d test_runner
```

Notes:
- If you prefer an automated loop generating traces continuously, `run_test_loop.sh` can be modified to include a `sleep` loop.
- The runner respects the `BASE_URL` env var; you can override it to target a different host: `docker-compose run --rm -e BASE_URL=http://host:8000 test_runner`.

## docker-compose.yml Documentation

### Version Declaration
```yaml
version: '3.8'
```
- Specifies Docker Compose file format
- Version 3.8 supports most modern features
- Note: Newer Docker versions ignore this but it's recommended for clarity

### Jaeger Service

#### Image
```yaml
image: jaegertracing/all-in-one:latest
```
- Official Jaeger all-in-one image
- Includes Jaeger agent, collector, and UI
- Latest tag ensures recent features

#### Ports
```yaml
ports:
  - "16686:16686"  # Jaeger UI
  - "4317:4317"    # OTLP gRPC receiver
  - "4318:4318"    # OTLP HTTP receiver
```
- **16686**: Web UI (http://localhost:16686)
- **4317**: OTLP gRPC protocol (used by our app)
- **4318**: OTLP HTTP protocol (alternative)
- Format: `host:container`

#### Environment Variables
```yaml
environment:
  - COLLECTOR_OTLP_ENABLED=true
```
- Enables OTLP collector for receiving spans
- Required for our OTEL exporter to work

#### Networking
```yaml
networks:
  - otel-network
```
- Connects to custom bridge network
- Allows service-to-service DNS resolution

### Python App Service

#### Build Configuration
```yaml
build:
  context: .
  dockerfile: Dockerfile
```
- **context**: Directory with Dockerfile and source code
- **dockerfile**: Path to Dockerfile
- Builds image from local files

#### Ports
```yaml
ports:
  - "8000:8000"
```
- Maps host port 8000 to container port 8000
- Access app at http://localhost:8000

#### Environment Variables
```yaml
environment:
  - OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
  - JAEGER_AGENT_HOST=jaeger
  - JAEGER_AGENT_PORT=6831
```
- **OTEL_EXPORTER_OTLP_ENDPOINT**: Points to Jaeger collector
- Uses service name "jaeger" (Docker DNS resolution)
- Port 4317 is OTLP gRPC protocol
- Other variables for compatibility

#### Dependencies
```yaml
depends_on:
  - jaeger
```
- Ensures Jaeger starts before Python app
- Docker Compose waits for container startup (not health)

#### Networking
```yaml
networks:
  - otel-network
```
- Connects to same network as Jaeger
- Enables hostname resolution (http://jaeger:4317)

### Custom Network
```yaml
networks:
  otel-network:
    driver: bridge
```
- **bridge**: Default driver, creates isolated network
- All containers can communicate by service name
- Better than default bridge for DNS resolution

### Service Communication Flow
```
python-app:8000 
    ↓ (OTLP gRPC)
jaeger:4317 (otel-network)
    ↓
Jaeger Collector
    ↓
Jaeger Storage
```

---

## Setup Instructions

### Prerequisites
- Docker Desktop installed and running
- Docker Compose installed (included with Docker Desktop)
- Python 3.11+ (for local test script execution)

### Step 1: Create Project Directory
```bash
mkdir python-otel-demo
cd python-otel-demo
```

### Step 2: Create Files
Place these files in the directory:
- `docker-compose.yml`
- `Dockerfile`
- `app.py`
- `requirements.txt`
- `test_app.py`

### Step 3: Start Containers
```bash
docker-compose up -d
```

### Step 4: Verify Services
```bash
docker-compose ps
```

Expected output:
```
NAME                          STATUS
python-otel-demo-jaeger-1    Up (healthy)
python-otel-demo-python-app-1 Up (healthy)
```

### Step 5: Test the App
```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "message": "Hello from OTEL Demo App!",
  "endpoints": ["/api/users", "/api/process", "/health"]
}
```

### Step 6: Generate Traces

Run locally:
```bash
pip install requests
python test_app.py
```

Run via the containerized test runner (recommended for compose setups):
```bash
# Build runner image
docker-compose build test_runner

# Run once and remove container after exit
docker-compose run --rm test_runner

# Or start the service (it will run once and exit)
docker-compose up --build -d test_runner
```

### Step 7: View Traces
1. Open http://localhost:16686
2. Select service: **python-demo-app**
3. Click **Find Traces**
4. Click on any trace to view details

---

## API Endpoints

### GET /
**Purpose**: Service information  
**Response**: JSON with endpoints list  
**Spans Created**: 1 (Flask auto-instrumentation)  
**Latency**: <10ms

### GET /api/users
**Purpose**: Simulate database query  
**Response**: List of user objects  
**Spans Created**: 2 (Flask + manual "fetch_users")  
**Attributes**:
- `db.system`: postgresql
- `db.operation`: select
- `result.count`: number of users
**Latency**: 100-300ms (simulated)

### GET /api/process
**Purpose**: Multi-step process with nested spans  
**Response**: Success status and duration  
**Spans Created**: 5 (Flask + parent + 3 child spans)
  - validate_data
  - process_data
  - save_results
**Attributes**:
- `step`: operation name
- `records_saved`: count of saved records
**Latency**: 200-700ms (simulated)

### GET /api/error
**Purpose**: Test error handling  
**Response**: Error message (HTTP 500)  
**Spans Created**: 1 with exception  
**Attributes**:
- `error`: true
**Exception**: ValueError with message

### GET /health
**Purpose**: Health check  
**Response**: {"status": "healthy"}  
**Spans Created**: 1 (Flask auto-instrumentation)  
**Latency**: <5ms

---

## Monitoring and Debugging

### View Logs

**Jaeger logs:**
```bash
docker-compose logs jaeger
```

**App logs:**
```bash
docker-compose logs python-app
```

**Real-time logs:**
```bash
docker-compose logs -f python-app
```

### Check Container Status
```bash
docker-compose ps
```

### Restart Services
```bash
docker-compose restart
```

### Stop Services
```bash
docker-compose down
```

### Remove Everything (including images)
```bash
docker-compose down --rmi all
```

### Jaeger UI Navigation

**1. Service Selection**
- Dropdown menu at top left
- Select "python-demo-app"

**2. Find Traces**
- Select operation (or "All")
- Adjust time range if needed
- Click "Find Traces"

**3. View Trace**
- Click on any trace row
- Shows full timeline of all spans
- Displays span attributes

**4. Span Details**
- Click on any span in timeline
- Shows start time, duration, attributes
- If error, shows exception details

**5. Trace Statistics**
- Shows min/max/avg duration
- Service count
- Operation count

### Common Issues and Solutions

**Issue: "Connection refused" when accessing http://localhost:16686**
- Solution: Ensure containers are running (`docker-compose ps`)
- Check Jaeger logs: `docker-compose logs jaeger`

**Issue: App can't reach Jaeger**
- Solution: Verify network: `docker network ls`
- Check endpoint: OTEL_EXPORTER_OTLP_ENDPOINT must be `http://jaeger:4317`

**Issue: No traces appear in Jaeger**
- Solution: Generate traces using test_app.py
- Check app logs: `docker-compose logs python-app`
- Verify COLLECTOR_OTLP_ENABLED=true in docker-compose.yml

**Issue: Container exits immediately**
- Solution: Check logs: `docker logs <container-name>`
- Common causes: import errors, environment variable issues

### Performance Tuning

**Batch Processing**: Spans are batched before sending
- Reduces network overhead
- Improves throughput
- Small latency cost (spans collected before export)

**Metric Reporting**: Metrics exported periodically
- Default: Every 60 seconds
- Configurable via MeterProvider

**Sampling**: Can be added to reduce trace volume
```python
from opentelemetry.sdk.trace.sampling import ProbabilitySampler
sampler = ProbabilitySampler(rate=0.1)  # 10% sampling
trace_provider = TracerProvider(sampler=sampler, resource=resource)
```

---

## Advanced Topics

### Adding Custom Instrumentation
```python
with tracer.start_as_current_span("custom_operation") as span:
    span.set_attribute("custom.field", "value")
    span.add_event("Important milestone reached")
    # your code here
```

### Adding Custom Metrics
```python
gauge = meter.create_gauge("app.custom.gauge", description="Custom gauge")
gauge.callback(lambda obs: obs.observe(42))
```

### Distributed Tracing (Multiple Services)
- Each service exports to same Jaeger
- Propagate trace context via HTTP headers
- Jaeger correlates traces across services

### Production Deployment
- Use persistent storage (Elasticsearch, Cassandra)
- Configure sampling for high-volume scenarios
- Set up alerts based on trace patterns
- Use different environment variables per deployment

---

## Additional Resources

- [OpenTelemetry Docs](https://opentelemetry.io/docs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [OTLP Specification](https://github.com/open-telemetry/opentelemetry-proto)
- [Flask Instrumentation](https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/flask/flask.html)

---

**Last Updated**: December 12, 2025  
**Version**: 1.0  
**Status**: Production Ready
