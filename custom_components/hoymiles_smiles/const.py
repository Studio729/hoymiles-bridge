"""Constants for the Hoymiles S-Miles integration."""
from datetime import timedelta
from typing import Final

DOMAIN: Final = "hoymiles_smiles"

# Configuration
CONF_HOST: Final = "host"
CONF_PORT: Final = "port"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# Defaults
DEFAULT_PORT: Final = 8080
DEFAULT_SCAN_INTERVAL: Final = 60  # seconds
DEFAULT_NAME: Final = "Hoymiles S-Miles"

# Update intervals
UPDATE_INTERVAL: Final = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

# API Endpoints
ENDPOINT_HEALTH: Final = "/health"
ENDPOINT_READY: Final = "/ready"
ENDPOINT_STATS: Final = "/stats"
ENDPOINT_METRICS: Final = "/metrics"
ENDPOINT_INVERTERS: Final = "/api/inverters"

# Sensor types
SENSOR_TYPES: Final = {
    "uptime": {
        "name": "Uptime",
        "icon": "mdi:clock-outline",
        "unit": "s",
        "device_class": "duration",
        "state_class": "total_increasing",
        "entity_category": None,
    },
    "messages_published": {
        "name": "MQTT Messages Published",
        "icon": "mdi:message-arrow-right",
        "unit": None,
        "device_class": None,
        "state_class": "total_increasing",
        "entity_category": None,
    },
    "mqtt_errors": {
        "name": "MQTT Errors",
        "icon": "mdi:alert-circle-outline",
        "unit": None,
        "device_class": None,
        "state_class": "total_increasing",
        "entity_category": None,
    },
    "dtu_query_count": {
        "name": "DTU Query Count",
        "icon": "mdi:counter",
        "unit": "queries",
        "device_class": None,
        "state_class": "total_increasing",
        "entity_category": None,
    },
    "dtu_error_count": {
        "name": "DTU Error Count",
        "icon": "mdi:alert-circle",
        "unit": "errors",
        "device_class": None,
        "state_class": "total_increasing",
        "entity_category": None,
    },
    "dtu_last_query": {
        "name": "DTU Last Query",
        "icon": "mdi:clock-check-outline",
        "unit": "s",
        "device_class": "duration",
        "state_class": None,
        "entity_category": None,
    },
    "database_size": {
        "name": "Database Size",
        "icon": "mdi:database",
        "unit": "MB",
        "device_class": None,
        "state_class": "measurement",
        "entity_category": "diagnostic",
    },
    "cached_records": {
        "name": "Cached Records",
        "icon": "mdi:database-check",
        "unit": "records",
        "device_class": None,
        "state_class": "measurement",
        "entity_category": "diagnostic",
    },
}

# Inverter-level sensor types (attached to inverter device)
INVERTER_SENSOR_TYPES: Final = {
    "grid_voltage": {
        "name": "Grid Voltage",
        "icon": "mdi:transmission-tower",
        "unit": "V",
        "device_class": "voltage",
        "state_class": "measurement",
        "entity_category": None,
    },
    "grid_frequency": {
        "name": "Grid Frequency",
        "icon": "mdi:sine-wave",
        "unit": "Hz",
        "device_class": "frequency",
        "state_class": "measurement",
        "entity_category": None,
    },
    "temperature": {
        "name": "Temperature",
        "icon": "mdi:thermometer",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "entity_category": None,
    },
    "operating_status": {
        "name": "Operating Status",
        "icon": "mdi:information-outline",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "entity_category": "diagnostic",
    },
    "link_status": {
        "name": "Link Status",
        "icon": "mdi:link-variant",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "entity_category": "diagnostic",
    },
    "alarm_code": {
        "name": "Alarm Code",
        "icon": "mdi:alert-circle",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "entity_category": "diagnostic",
    },
    "alarm_count": {
        "name": "Alarm Count",
        "icon": "mdi:counter",
        "unit": None,
        "device_class": None,
        "state_class": "total_increasing",
        "entity_category": "diagnostic",
    },
}

# DTU-level sensor types (attached to DTU device)
DTU_SENSOR_TYPES: Final = {
    "inverter_count": {
        "name": "Inverter Count",
        "icon": "mdi:counter",
        "unit": "inverters",
        "device_class": None,
        "state_class": "measurement",
        "entity_category": None,
    },
    "last_query_time": {
        "name": "Last Query Time",
        "icon": "mdi:clock-check",
        "unit": None,
        "device_class": "timestamp",
        "state_class": None,
        "entity_category": "diagnostic",
    },
    "query_count": {
        "name": "Query Count",
        "icon": "mdi:counter",
        "unit": "queries",
        "device_class": None,
        "state_class": "total_increasing",
        "entity_category": "diagnostic",
    },
    "error_count": {
        "name": "Error Count",
        "icon": "mdi:alert-circle",
        "unit": "errors",
        "device_class": None,
        "state_class": "total_increasing",
        "entity_category": "diagnostic",
    },
    "communication_status": {
        "name": "Communication Status",
        "icon": "mdi:network",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "entity_category": "diagnostic",
    },
    "total_power": {
        "name": "Total Power",
        "icon": "mdi:lightning-bolt",
        "unit": "W",
        "device_class": "power",
        "state_class": "measurement",
        "entity_category": None,
    },
}

# Aggregate sensors at inverter level (sum of all ports)
INVERTER_AGGREGATE_SENSORS: Final = {
    "total_power": {
        "name": "Total Power",
        "icon": "mdi:lightning-bolt",
        "unit": "W",
        "device_class": "power",
        "state_class": "measurement",
        "entity_category": None,
    },
    "total_today_production": {
        "name": "Total Today Production",
        "icon": "mdi:solar-power",
        "unit": "Wh",
        "device_class": "energy",
        "state_class": "total_increasing",
        "entity_category": None,
    },
    "total_lifetime_production": {
        "name": "Total Lifetime Production",
        "icon": "mdi:solar-power",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
        "entity_category": None,
    },
}

# Port-level sensor types (attached to port device)
PORT_SENSOR_TYPES: Final = {
    "pv_voltage": {
        "name": "PV Voltage",
        "icon": "mdi:lightning-bolt",
        "unit": "V",
        "device_class": "voltage",
        "state_class": "measurement",
        "entity_category": None,
    },
    "pv_current": {
        "name": "PV Current",
        "icon": "mdi:current-dc",
        "unit": "A",
        "device_class": "current",
        "state_class": "measurement",
        "entity_category": None,
    },
    "pv_power": {
        "name": "PV Power",
        "icon": "mdi:solar-power",
        "unit": "W",
        "device_class": "power",
        "state_class": "measurement",
        "entity_category": None,
    },
    "today_production": {
        "name": "Today Production",
        "icon": "mdi:solar-power",
        "unit": "Wh",
        "device_class": "energy",
        "state_class": "total_increasing",
        "entity_category": None,
    },
    "total_production": {
        "name": "Total Production",
        "icon": "mdi:solar-power",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
        "entity_category": None,
    },
}

# Binary sensor types
BINARY_SENSOR_TYPES: Final = {
    "healthy": {
        "name": "Application Healthy",
        "icon": "mdi:check-circle",
        "icon_off": "mdi:alert-circle",
        "device_class": "connectivity",
        "entity_category": None,
    },
}

# Attributes
ATTR_START_TIME: Final = "start_time"
ATTR_DTU_STATUS: Final = "dtu_status"
ATTR_DTU_LAST_ERROR: Final = "dtu_last_error"
ATTR_DTU_LAST_ERROR_TIME: Final = "dtu_last_error_time"
ATTR_CIRCUIT_BREAKER_STATE: Final = "circuit_breaker_state"

