# Web Server / Health Endpoint Configuration

The application includes an optional built-in web server that provides health checks, metrics, and statistics endpoints.

## Environment Variable

### `HEALTH_PORT`
**Description:** Port number for the web server endpoint  
**Default:** `8080`  
**Valid Range:** `1-65535`  
**Type:** Integer

## Docker Compose Configuration

### Set Custom Port

```yaml
services:
  hoymiles_mqtt:
    environment:
      HEALTH_ENABLED: true
      HEALTH_PORT: 9090        # Use port 9090 instead of default 8080
```

### Common Port Configurations

#### Default (Port 8080)
```yaml
environment:
  HEALTH_ENABLED: true
  HEALTH_PORT: 8080
```
Access: `http://your-ip:8080/health`

#### Custom Port (Port 9090)
```yaml
environment:
  HEALTH_ENABLED: true
  HEALTH_PORT: 9090
```
Access: `http://your-ip:9090/health`

#### Different Port for Each Service
```yaml
environment:
  HEALTH_ENABLED: true
  HEALTH_PORT: 8081
```
Access: `http://your-ip:8081/health`

#### Disable Web Server
```yaml
environment:
  HEALTH_ENABLED: false
```
No web server will start.

## Network Modes

### With Host Mode (Your Setup)
When using `network_mode: host`, the port is directly accessible on the host:

```yaml
services:
  hoymiles_mqtt:
    network_mode: host
    environment:
      HEALTH_PORT: 8080
```

**Access:**
- `http://localhost:8080/health`
- `http://127.0.0.1:8080/health`
- `http://192.168.1.31:8080/health` (your host IP)

**No port mapping needed!** The service binds directly to the host port.

### With Bridge Mode (Default Docker)
When using bridge networking, you need to expose the port:

```yaml
services:
  hoymiles_mqtt:
    environment:
      HEALTH_PORT: 8080
    ports:
      - "8080:8080"         # host:container
      # or different host port:
      - "9090:8080"         # Access on host port 9090, container uses 8080
```

## Available Endpoints

Once the web server is running, these endpoints are available:

### `/health` - Health Status
```bash
curl http://localhost:8080/health
```

**Returns:**
```json
{
  "healthy": true,
  "uptime_seconds": 3600,
  "dtus": {
    "DTU": {
      "status": "online",
      "last_successful_query": "2024-01-01T12:00:00",
      "query_count": 60
    }
  }
}
```

### `/ready` - Readiness Probe
```bash
curl http://localhost:8080/ready
```

**Returns:**
- `200 OK` if healthy
- `503 Service Unavailable` if not ready

Great for Kubernetes liveness/readiness probes.

### `/metrics` - Prometheus Metrics
```bash
curl http://localhost:8080/metrics
```

**Returns:** Prometheus-formatted metrics

### `/stats` - Database Statistics
```bash
curl http://localhost:8080/stats
```

**Returns:**
```json
{
  "database_path": "/data/hoymiles-mqtt.db",
  "database_size_bytes": 12288,
  "production_cache_entries": 4,
  "metrics_entries": 120
}
```

## Examples

### Example 1: Default Setup (Port 8080)
```yaml
version: "3"

services:
  hoymiles_mqtt:
    container_name: "hoymiles_mqtt"
    image: hoymiles_mqtt
    network_mode: host
    environment:
      MQTT_BROKER: 192.168.1.31
      DTU_HOST: 192.168.1.194
      HEALTH_ENABLED: true
      HEALTH_PORT: 8080          # Default port
```

**Test:**
```bash
curl http://192.168.1.31:8080/health
```

### Example 2: Custom Port (Port 9000)
```yaml
version: "3"

services:
  hoymiles_mqtt:
    container_name: "hoymiles_mqtt"
    image: hoymiles_mqtt
    network_mode: host
    environment:
      MQTT_BROKER: 192.168.1.31
      DTU_HOST: 192.168.1.194
      HEALTH_ENABLED: true
      HEALTH_PORT: 9000          # Custom port
```

**Test:**
```bash
curl http://192.168.1.31:9000/health
```

### Example 3: Disabled Web Server
```yaml
version: "3"

services:
  hoymiles_mqtt:
    container_name: "hoymiles_mqtt"
    image: hoymiles_mqtt
    network_mode: host
    environment:
      MQTT_BROKER: 192.168.1.31
      DTU_HOST: 192.168.1.194
      HEALTH_ENABLED: false      # No web server
```

No endpoints available.

### Example 4: Multiple Instances on Different Ports
```yaml
version: "3"

services:
  hoymiles_mqtt_1:
    container_name: "hoymiles_mqtt_1"
    image: hoymiles_mqtt
    network_mode: host
    environment:
      MQTT_BROKER: 192.168.1.31
      DTU_HOST: 192.168.1.194
      HEALTH_PORT: 8081          # Instance 1 on port 8081

  hoymiles_mqtt_2:
    container_name: "hoymiles_mqtt_2"
    image: hoymiles_mqtt
    network_mode: host
    environment:
      MQTT_BROKER: 192.168.1.31
      DTU_HOST: 192.168.1.195
      HEALTH_PORT: 8082          # Instance 2 on port 8082
```

**Test:**
```bash
curl http://192.168.1.31:8081/health  # Instance 1
curl http://192.168.1.31:8082/health  # Instance 2
```

## Port Conflicts

### Check if Port is in Use
```bash
# Linux/Mac
sudo lsof -i :8080

# Or use netstat
netstat -tuln | grep 8080

# Docker
docker ps --format "{{.Names}}: {{.Ports}}"
```

### Change Port if Conflict
If port 8080 is already in use:

```yaml
environment:
  HEALTH_PORT: 8888    # Use any available port
```

### Common Port Conflicts
- **8080** - Often used by other services (Jenkins, Tomcat, etc.)
- **8081** - Alternative HTTP port
- **9090** - Prometheus default
- **3000** - Grafana default

**Solution:** Pick an unused port in your environment.

## Firewall Configuration

If you can't access the endpoint from another machine:

### Allow Port in Firewall (Linux)
```bash
sudo ufw allow 8080/tcp
```

### Allow Port in Firewall (Docker host)
```bash
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
```

### Test from Another Machine
```bash
curl http://192.168.1.31:8080/health
```

## Kubernetes Configuration

### Liveness Probe
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 30
```

### Readiness Probe
```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10
```

### Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: hoymiles-mqtt
spec:
  selector:
    app: hoymiles-mqtt
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
```

## Monitoring Integration

### Prometheus Scrape Config
```yaml
scrape_configs:
  - job_name: 'hoymiles-mqtt'
    static_configs:
      - targets: ['192.168.1.31:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### Grafana Data Source
1. Add Prometheus data source
2. Prometheus will scrape metrics from `http://192.168.1.31:8080/metrics`
3. Create dashboards using the metrics

## Security Considerations

### Expose Only Locally
```yaml
environment:
  HEALTH_HOST: 127.0.0.1    # Only accessible from localhost
  HEALTH_PORT: 8080
```

### Expose to Specific Network (Bridge Mode)
```yaml
services:
  hoymiles_mqtt:
    networks:
      - internal-network
    ports:
      - "127.0.0.1:8080:8080"  # Only accessible from localhost
```

### Use Reverse Proxy
Put nginx or Caddy in front for:
- Authentication
- SSL/TLS
- Rate limiting
- Access control

## Troubleshooting

### Web Server Not Starting
```bash
# Check logs
docker-compose logs hoymiles_mqtt | grep -i health

# Common issues:
# 1. Port already in use -> Change HEALTH_PORT
# 2. HEALTH_ENABLED=false -> Set to true
# 3. Permission denied -> Use port > 1024
```

### Can't Access from Another Machine
```bash
# 1. Check if service is listening
docker-compose exec hoymiles_mqtt netstat -tuln | grep 8080

# 2. Check firewall
sudo ufw status

# 3. Test locally first
docker-compose exec hoymiles_mqtt curl http://localhost:8080/health

# 4. Test from host
curl http://localhost:8080/health

# 5. Test from another machine
curl http://192.168.1.31:8080/health
```

### Different Port Not Working
```bash
# Verify environment variable is set
docker-compose exec hoymiles_mqtt env | grep HEALTH_PORT

# Restart after changing
docker-compose restart hoymiles_mqtt

# Check logs for the port being used
docker-compose logs hoymiles_mqtt | grep "Health check server started"
```

## Complete Example

Your original setup enhanced with web server configuration:

```yaml
version: "3"

services:
  hoymiles_mqtt:
    container_name: "hoymiles_mqtt"
    image: hoymiles_mqtt
    network_mode: host
    environment:
      # Required
      MQTT_BROKER: 192.168.1.31
      DTU_HOST: 192.168.1.194
      MICROINVERTER_TYPE: 'HM'
      QUERY_PERIOD: 300
      
      # Web Server Configuration
      HEALTH_ENABLED: true
      HEALTH_PORT: 8080          # ← Set your preferred port here
      METRICS_ENABLED: true
      
      # Optional: Other settings
      PERSISTENCE_ENABLED: true
      LOG_LEVEL: INFO
      TIMEZONE: America/New_York
    
    volumes:
      - ./data:/data
    
    labels:
      - "com.centurylinklabs.watchtower.enable=false"
    
    restart: unless-stopped
```

**Access endpoints:**
```bash
# Health check
curl http://192.168.1.31:8080/health

# Metrics
curl http://192.168.1.31:8080/metrics

# Database stats
curl http://192.168.1.31:8080/stats

# Readiness probe
curl http://192.168.1.31:8080/ready
```

## Summary

| Variable | Default | Description |
|----------|---------|-------------|
| `HEALTH_ENABLED` | `true` | Enable/disable web server |
| `HEALTH_PORT` | `8080` | Port for web server (1-65535) |
| `HEALTH_HOST` | `0.0.0.0` | Host to bind to |
| `METRICS_ENABLED` | `true` | Enable Prometheus metrics |

**Quick Configuration:**
```yaml
environment:
  HEALTH_PORT: 8080  # Change to any port you want (e.g., 9090, 8888, etc.)
```

The web server will start automatically and be accessible at:
`http://your-ip:PORT/health`

