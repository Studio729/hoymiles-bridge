# Recommendations for Improvement

## Architecture Improvements

### 1. Add Database Connection Pooling Management
**Current State**: Basic psycopg2 connection pooling
**Recommendation**: 
- Implement connection health checks
- Add automatic connection recovery
- Monitor pool utilization via Prometheus metrics
- Consider using SQLAlchemy for better ORM support

```python
# Example enhancement
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    f"postgresql://{user}:{password}@{host}:{port}/{database}",
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections after 1 hour
)
```

### 2. Implement Database Partitioning
**Issue**: As data grows, queries will slow down
**Recommendation**: Partition time-series tables by time period

```sql
-- Example: Partition inverter_data by month
CREATE TABLE inverter_data (
    id BIGSERIAL,
    timestamp TIMESTAMP NOT NULL,
    ...
) PARTITION BY RANGE (timestamp);

CREATE TABLE inverter_data_2024_01 
    PARTITION OF inverter_data 
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### 3. Add Database Indexing Strategy
**Recommendation**: Create additional indexes for common queries

```sql
-- Composite indexes for common queries
CREATE INDEX idx_inverter_data_serial_time 
    ON inverter_data(serial_number, timestamp DESC);

CREATE INDEX idx_port_data_serial_port_time 
    ON port_data(serial_number, port_number, timestamp DESC);

-- Partial indexes for recent data queries
CREATE INDEX idx_inverter_data_recent 
    ON inverter_data(timestamp DESC) 
    WHERE timestamp > NOW() - INTERVAL '7 days';
```

## Data Management

### 4. Implement Data Retention Policies (Optional)
**Current**: All data retained permanently
**Recommendation**: Add configurable retention policies for different data types

```yaml
retention_policies:
  raw_data: 90d          # Keep raw readings for 90 days
  hourly_aggregates: 1y  # Keep hourly aggregates for 1 year
  daily_aggregates: 5y   # Keep daily aggregates for 5 years
  monthly_aggregates: forever
```

### 5. Add Data Aggregation
**Benefit**: Faster queries for dashboards and reports
**Recommendation**: Create materialized views or aggregation tables

```sql
-- Hourly aggregates
CREATE MATERIALIZED VIEW hourly_production AS
SELECT 
    date_trunc('hour', timestamp) as hour,
    serial_number,
    port_number,
    AVG(pv_power) as avg_power,
    SUM(today_production) as production
FROM port_data
GROUP BY hour, serial_number, port_number;

-- Refresh hourly
CREATE INDEX ON hourly_production(hour DESC);
```

### 6. Implement Backup Strategy
**Critical**: Add automated database backups
**Recommendation**:

```yaml
# Add to docker-compose.yml
services:
  postgres-backup:
    image: prodrigestivill/postgres-backup-local
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_DB: hoymiles
      POSTGRES_USER: hoymiles
      POSTGRES_PASSWORD: hoymiles_password
      SCHEDULE: "@daily"
      BACKUP_KEEP_DAYS: 7
      BACKUP_KEEP_WEEKS: 4
      BACKUP_KEEP_MONTHS: 6
    volumes:
      - ./backups:/backups
    depends_on:
      - postgres
```

## API Enhancements

### 7. Add API Authentication
**Current**: Open API endpoints
**Recommendation**: Add token-based authentication

```python
# Example: Simple token auth
def verify_token(token: str) -> bool:
    return token == os.getenv('API_TOKEN')

def _handle_api(self):
    auth_header = self.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        self.send_error(401, "Unauthorized")
        return
    
    token = auth_header.split(' ')[1]
    if not verify_token(token):
        self.send_error(403, "Forbidden")
        return
    # ... rest of API handling
```

### 8. Add API Rate Limiting
**Protection**: Prevent API abuse
**Recommendation**: Implement rate limiting per IP/token

```python
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, requests_per_minute=60):
        self.requests = defaultdict(list)
        self.limit = requests_per_minute
    
    def is_allowed(self, client_id: str) -> bool:
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        
        # Remove old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > cutoff
        ]
        
        # Check limit
        if len(self.requests[client_id]) >= self.limit:
            return False
        
        self.requests[client_id].append(now)
        return True
```

### 9. Add GraphQL API Option
**Benefit**: Flexible data queries for Home Assistant and other clients
**Recommendation**: Consider adding GraphQL alongside REST API

```python
# Example with graphene
import graphene

class InverterType(graphene.ObjectType):
    serial_number = graphene.String()
    grid_voltage = graphene.Float()
    temperature = graphene.Float()
    
class Query(graphene.ObjectType):
    inverters = graphene.List(InverterType)
    
    def resolve_inverters(self, info):
        return persistence.get_all_inverters()
```

## Performance Optimizations

### 10. Add Caching Layer
**Benefit**: Reduce database load for frequently accessed data
**Recommendation**: Add Redis for caching

```python
import redis

cache = redis.Redis(host='redis', port=6379, decode_responses=True)

def get_latest_inverter_data(serial_number: str):
    # Check cache first
    cache_key = f"inverter:{serial_number}:latest"
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Query database
    data = persistence.get_latest_inverter_data(serial_number, limit=1)
    
    # Cache for 60 seconds
    cache.setex(cache_key, 60, json.dumps(data))
    return data
```

### 11. Implement Async Database Operations
**Current**: Synchronous psycopg2
**Recommendation**: Switch to asyncpg for better performance

```python
import asyncpg

class AsyncPersistenceManager:
    async def initialize(self):
        self.pool = await asyncpg.create_pool(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
            min_size=5,
            max_size=20,
        )
    
    async def save_inverter_data(self, serial_number, data):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO inverter_data (serial_number, grid_voltage, ...)
                VALUES ($1, $2, ...)
            ''', serial_number, data['grid_voltage'], ...)
```

## Home Assistant Integration

### 12. Add Real-time Updates via WebSocket
**Current**: Polling-based updates
**Recommendation**: Add WebSocket support for real-time updates

```python
import websockets
import json

async def websocket_handler(websocket, path):
    """Send real-time updates to connected clients."""
    try:
        while True:
            # Wait for new data
            data = await data_queue.get()
            await websocket.send(json.dumps(data))
    except websockets.ConnectionClosed:
        pass
```

### 13. Add Historical Data Sensors
**Recommendation**: Create sensors that show historical trends

```python
# In custom component
class HoymilesHistoricalSensor:
    """Sensor showing historical data (7-day average, etc.)."""
    
    async def async_update(self):
        """Fetch historical data from API."""
        response = await self.session.get(
            f"{self.base_url}/api/inverters/{self.serial}/history?limit=168"
        )
        data = await response.json()
        
        # Calculate 7-day average
        self._state = statistics.mean([d['pv_power'] for d in data])
```

## Monitoring & Observability

### 14. Add Structured Logging
**Current**: Standard Python logging
**Recommendation**: Use structured logging for better log analysis

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "inverter_data_saved",
    serial_number=serial_number,
    dtu_name=dtu_name,
    voltage=data.get('grid_voltage'),
    temperature=data.get('temperature'),
)
```

### 15. Add Distributed Tracing
**Recommendation**: Add OpenTelemetry for request tracing

```python
from opentelemetry import trace
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("query_dtu"):
    plant_data = self.modbus_client.read_plant_data()
    
    with tracer.start_as_current_span("save_to_database"):
        self.persistence.save_inverter_data(...)
```

### 16. Enhance Prometheus Metrics
**Recommendation**: Add more detailed metrics

```python
from prometheus_client import Summary, Histogram

# Database operation metrics
DB_OPERATION_DURATION = Histogram(
    'hoymiles_db_operation_duration_seconds',
    'Database operation duration',
    ['operation', 'table']
)

DB_POOL_SIZE = Gauge(
    'hoymiles_db_pool_size',
    'Database connection pool size',
    ['state']  # active, idle
)

API_REQUEST_DURATION = Histogram(
    'hoymiles_api_request_duration_seconds',
    'API request duration',
    ['endpoint', 'method', 'status']
)
```

## Security

### 17. Add SSL/TLS for Database Connections
**Recommendation**: Encrypt database connections

```python
db_config = {
    'host': host,
    'port': port,
    'sslmode': 'require',
    'sslrootcert': '/path/to/ca-cert.pem',
    'sslcert': '/path/to/client-cert.pem',
    'sslkey': '/path/to/client-key.pem',
}
```

### 18. Implement Secrets Management
**Recommendation**: Use secrets manager instead of environment variables

```python
# Example with Docker secrets
def get_secret(secret_name):
    secret_path = f"/run/secrets/{secret_name}"
    if os.path.exists(secret_path):
        with open(secret_path) as f:
            return f.read().strip()
    return os.getenv(secret_name.upper())

db_password = get_secret('db_password')
```

## Testing & Quality

### 19. Add Integration Tests
**Recommendation**: Add comprehensive test suite

```python
# tests/test_integration.py
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture
def postgres():
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres

def test_persistence_manager(postgres):
    manager = PersistenceManager(
        host=postgres.get_container_host_ip(),
        port=postgres.get_exposed_port(5432),
        ...
    )
    
    # Test operations
    manager.save_inverter_data(...)
    data = manager.get_latest_inverter_data(...)
    assert data is not None
```

### 20. Add API Documentation
**Recommendation**: Generate OpenAPI/Swagger documentation

```python
# Add to health server
def _handle_swagger(self):
    """Serve OpenAPI documentation."""
    swagger_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Hoymiles S-Miles API",
            "version": "2.0.0"
        },
        "paths": {
            "/api/inverters": {
                "get": {
                    "summary": "List all inverters",
                    "responses": {
                        "200": {
                            "description": "List of inverters"
                        }
                    }
                }
            }
        }
    }
    self._send_json_response(swagger_spec)
```

## Priority Recommendations

### High Priority (Implement First)
1. ✅ Database connection pooling management (#1)
2. ✅ Database backups (#6)
3. ✅ API authentication (#7)
4. ✅ Structured logging (#14)
5. ✅ Integration tests (#19)

### Medium Priority
6. Database partitioning (#2)
7. Data aggregation (#5)
8. Caching layer (#10)
9. Enhanced Prometheus metrics (#16)
10. API documentation (#20)

### Low Priority (Future Enhancements)
11. GraphQL API (#9)
12. WebSocket support (#12)
13. Distributed tracing (#15)
14. Async database operations (#11)

## Conclusion

These recommendations will help create a more robust, scalable, and maintainable system. Implement them incrementally based on your specific needs and priorities.

