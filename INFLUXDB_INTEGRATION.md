# InfluxDB v3 Integration Guide

## Overview

The Hoymiles S-Miles Bridge now supports **optional integration with InfluxDB v3** for time-series data storage and visualization.

## Features

✅ **Real-time Data Push** - Solar production data pushed to InfluxDB as it's collected  
✅ **Three Data Types** - DTU, Inverter, and Port/Panel measurements  
✅ **Automatic Tagging** - Data tagged by DTU name, serial numbers, port numbers  
✅ **Optional** - Runs alongside existing database persistence  
✅ **InfluxDB v3 Compatible** - Uses Apache Arrow-based InfluxDB 3.0 API  

## What Gets Sent to InfluxDB

### 1. DTU-Level Data (Measurement: `dtu`)
Aggregated data across all inverters:
- `pv_power` (float) - Total current power production (W)
- `today_production` (int) - Today's total energy (Wh)
- `total_production` (int) - Lifetime total energy (Wh)
- `alarm_flag` (boolean) - Any inverters with alarms

**Tags**: `dtu_name`, `dtu_serial`

### 2. Inverter Data (Measurement: `inverter`)
Per-inverter metrics:
- `grid_voltage` (float) - Grid voltage (V)
- `grid_frequency` (float) - Grid frequency (Hz)
- `temperature` (float) - Inverter temperature (°C)
- `operating_status` (int) - Operating status code
- `alarm_code` (int) - Alarm code
- `alarm_count` (int) - Number of alarms
- `link_status` (int) - Link status

**Tags**: `serial_number`, `dtu_name`

### 3. Port/Panel Data (Measurement: `port`)
Per-port/panel metrics:
- `pv_voltage` (float) - PV voltage (V)
- `pv_current` (float) - PV current (A)
- `pv_power` (float) - PV power (W)
- `today_production` (int) - Today's energy (Wh)
- `total_production` (int) - Lifetime energy (Wh)

**Tags**: `serial_number`, `port_number`, `dtu_name`

## Configuration

### Environment Variables

Add these to your `.env` file or Docker Compose:

```env
# Enable InfluxDB integration
INFLUXDB_ENABLED=true

# InfluxDB host URL (required)
INFLUXDB_HOST=https://influxdb3.suttonclan.org

# API token (required)
INFLUXDB_TOKEN=apiv3_hON1-RyMEHu7B8EqUUniMr2V8F9S7tlkI2p0Z-LlKs65vcq8RfBvIZlQ_UI00jYB8n5XocgIDhAPTpjTAqvg6Q

# Database/bucket name (optional, defaults to "hoymiles")
INFLUXDB_DATABASE=hoymiles

# Organization (optional for InfluxDB v3)
INFLUXDB_ORG=
```

### Docker Compose Example

```yaml
services:
  hoymiles-smiles:
    image: ghcr.io/studio729/hoymiles-bridge:latest
    environment:
      # ... other variables ...
      
      # InfluxDB v3 Integration
      INFLUXDB_ENABLED: true
      INFLUXDB_HOST: https://influxdb3.suttonclan.org
      INFLUXDB_TOKEN: apiv3_hON1-RyMEHu7B8EqUUniMr2V8F9S7tlkI2p0Z-LlKs65vcq8RfBvIZlQ_UI00jYB8n5XocgIDhAPTpjTAqvg6Q
      INFLUXDB_DATABASE: hoymiles
```

## Setup Instructions

### Step 1: Enable InfluxDB

Update your `.env` file:

```bash
cd /Users/tim/Projects/hoymiles-bridge
nano .env
```

Add:
```env
INFLUXDB_ENABLED=true
INFLUXDB_HOST=https://influxdb3.suttonclan.org
INFLUXDB_TOKEN=apiv3_hON1-RyMEHu7B8EqUUniMr2V8F9S7tlkI2p0Z-LlKs65vcq8RfBvIZlQ_UI00jYB8n5XocgIDhAPTpjTAqvg6Q
INFLUXDB_DATABASE=hoymiles
```

### Step 2: Rebuild Docker Image

```bash
docker-compose build --no-cache
```

### Step 3: Restart Container

```bash
docker-compose down
docker-compose up -d
```

### Step 4: Verify

Check logs:
```bash
docker logs hoymiles-smiles | grep -i influx
```

Should see:
```
InfluxDB writer initialized: https://influxdb3.suttonclan.org/hoymiles
```

## Querying Data

### Using InfluxDB SQL

InfluxDB v3 supports SQL queries:

```sql
-- Get latest power readings
SELECT time, dtu_name, pv_power
FROM dtu
WHERE time > now() - interval '1 hour'
ORDER BY time DESC
LIMIT 100;

-- Get inverter temperatures
SELECT time, serial_number, temperature
FROM inverter
WHERE time > now() - interval '1 day'
ORDER BY time DESC;

-- Get port production
SELECT time, serial_number, port_number, pv_power, today_production
FROM port
WHERE time > now() - interval '6 hours'
ORDER BY time DESC;
```

### Using Python Client

```python
from influxdb_client_3 import InfluxDBClient3

client = InfluxDBClient3(
    host="https://influxdb3.suttonclan.org",
    token="your_token_here",
    database="hoymiles"
)

# Query latest power
query = """
SELECT time, dtu_name, pv_power
FROM dtu
WHERE time > now() - interval '1 hour'
ORDER BY time DESC
"""

table = client.query(query)
print(table.to_pandas())
```

## Grafana Visualization

Create beautiful dashboards in Grafana:

### Panel 1: Current Power Production
```sql
SELECT 
  time,
  dtu_name,
  pv_power
FROM dtu
WHERE time > now() - interval '24 hours'
ORDER BY time ASC
```

### Panel 2: Daily Production
```sql
SELECT 
  time_bucket(INTERVAL '1 hour', time) as hour,
  MAX(today_production) - MIN(today_production) as production_wh
FROM dtu
WHERE time > now() - interval '24 hours'
GROUP BY hour
ORDER BY hour ASC
```

### Panel 3: Inverter Temperature
```sql
SELECT 
  time,
  serial_number,
  temperature
FROM inverter
WHERE time > now() - interval '6 hours'
ORDER BY time ASC
```

## Data Retention

InfluxDB v3 handles retention policies automatically. Configure in your InfluxDB instance:

- **Short-term** (high resolution): Keep all data for 7 days
- **Medium-term** (downsampled): Hourly averages for 90 days
- **Long-term** (downsampled): Daily totals forever

## Troubleshooting

### Connection Refused

**Error**: `Failed to initialize InfluxDB client: Connection refused`

**Solutions**:
1. Verify host URL is correct and accessible
2. Test connectivity: `curl https://influxdb3.suttonclan.org`
3. Check firewall rules

### Authentication Failed

**Error**: `Failed to initialize InfluxDB client: 401 Unauthorized`

**Solutions**:
1. Verify API token is correct
2. Check token permissions in InfluxDB
3. Ensure token hasn't expired

### No Data in InfluxDB

**Checklist**:
1. Verify `INFLUXDB_ENABLED=true` in environment
2. Check logs: `docker logs hoymiles-smiles`
3. Verify database name matches
4. Ensure DTU is actually producing data

### InfluxDB Writer Failed to Initialize

**Error**: `InfluxDB writer failed to initialize`

**Solutions**:
1. Check if `influxdb3-python` package is installed
2. Rebuild Docker image: `docker-compose build --no-cache`
3. Verify all required environment variables are set

## Performance Considerations

- **Write Rate**: Data written every query period (default: 60 seconds)
- **Batch Writes**: Each query writes 1 DTU measurement + N inverter measurements + N port measurements
- **Network**: Minimal overhead, uses efficient binary protocol
- **Database Impact**: InfluxDB writes don't affect main database performance

## Security Best Practices

### Protect Your API Token

**Don't**: Commit tokens to Git
```bash
# Add to .gitignore
echo ".env" >> .gitignore
```

**Do**: Use environment variables
```yaml
environment:
  INFLUXDB_TOKEN: ${INFLUXDB_TOKEN}  # Read from host environment
```

**Do**: Use secrets management
```yaml
environment:
  INFLUXDB_TOKEN_FILE: /run/secrets/influxdb_token
secrets:
  influxdb_token:
    external: true
```

### Rotate Tokens Regularly

1. Generate new token in InfluxDB
2. Update `.env` file
3. Restart container
4. Delete old token in InfluxDB

## Disabling InfluxDB

To disable InfluxDB integration:

```env
INFLUXDB_ENABLED=false
```

Or remove the environment variables entirely. The application will continue to work normally without InfluxDB.

## Files Modified

- ✏️ `hoymiles_smiles/config.py` - Added InfluxDBConfig
- ✏️ `hoymiles_smiles/runners.py` - Integrated InfluxDB writes
- ✏️ `hoymiles_smiles/__main__.py` - Initialize InfluxDB writer
- ✏️ `pyproject.toml` - Added influxdb3-python dependency
- ✏️ `env.example` - Added InfluxDB variables
- ✏️ `docker-compose.yml` - Added InfluxDB environment variables
- ✨ **NEW** `hoymiles_smiles/influxdb_client.py` - InfluxDB writer

## Example Queries

### Total Production by DTU
```sql
SELECT 
  dtu_name,
  MAX(total_production) as lifetime_production_wh
FROM dtu
GROUP BY dtu_name
```

### Average Power by Hour
```sql
SELECT 
  time_bucket(INTERVAL '1 hour', time) as hour,
  AVG(pv_power) as avg_power_w
FROM dtu
WHERE time > now() - interval '7 days'
GROUP BY hour
ORDER BY hour ASC
```

### Inverter Uptime
```sql
SELECT 
  serial_number,
  COUNT(*) as measurements,
  MAX(time) - MIN(time) as uptime
FROM inverter
WHERE time > now() - interval '24 hours'
GROUP BY serial_number
```

### Port Performance Comparison
```sql
SELECT 
  port_number,
  AVG(pv_power) as avg_power,
  MAX(pv_power) as peak_power
FROM port
WHERE time > now() - interval '24 hours'
GROUP BY port_number
ORDER BY avg_power DESC
```

## Benefits

✅ **Long-term Analytics** - Years of high-resolution data  
✅ **Real-time Dashboards** - Grafana visualization  
✅ **Fast Queries** - Optimized time-series database  
✅ **Flexible** - SQL queries, Python, API access  
✅ **Scalable** - Handles millions of data points  
✅ **Industry Standard** - Used by thousands of IoT applications  

## Support

For InfluxDB-specific issues:
- **InfluxDB Docs**: https://docs.influxdata.com/
- **Community**: https://community.influxdata.com/

For integration issues:
- Check container logs: `docker logs hoymiles-smiles`
- Open GitHub issue with log excerpts

---

**Version**: Added in v1.2.0  
**Date**: November 7, 2025  
**Status**: Production Ready ✅

