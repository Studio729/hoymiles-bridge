"""Constants for the Hoymiles MQTT Bridge integration."""
from datetime import timedelta
from typing import Final

DOMAIN: Final = "hoymiles_mqtt"

# Configuration
CONF_HOST: Final = "host"
CONF_PORT: Final = "port"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# Defaults
DEFAULT_PORT: Final = 8090
DEFAULT_SCAN_INTERVAL: Final = 60  # seconds
DEFAULT_NAME: Final = "Hoymiles MQTT"

# Update intervals
UPDATE_INTERVAL: Final = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

# API Endpoints
ENDPOINT_HEALTH: Final = "/health"
ENDPOINT_READY: Final = "/ready"
ENDPOINT_STATS: Final = "/stats"
ENDPOINT_METRICS: Final = "/metrics"

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

