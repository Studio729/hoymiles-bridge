"""Top-level package for Hoymiles MQTT."""

import logging

__author__ = """Mariusz Wasiluk"""
__email__ = 'foo@bar.com'
__version__ = '0.12.0'

MI_ENTITIES = [
    'grid_voltage',
    'grid_frequency',
    'temperature',
    'operating_status',
    'alarm_code',
    'alarm_count',
    'link_status',
]

PORT_ENTITIES = ['pv_voltage', 'pv_current', 'pv_power', 'today_production', 'total_production']

_main_logger = logging.getLogger(__name__)

# Expose main configuration classes
from hoymiles_mqtt.config import AppConfig, DatabaseConfig, DtuConfig

__all__ = [
    '__version__',
    'MI_ENTITIES',
    'PORT_ENTITIES',
    'AppConfig',
    'DtuConfig',
    'DatabaseConfig',
]
