"""Configuration management with Pydantic validation."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DtuConfig(BaseModel):
    """Configuration for a single DTU."""

    name: str = Field(default="DTU", description="Friendly name for the DTU")
    host: str = Field(..., description="DTU hostname or IP address")
    port: int = Field(default=502, ge=1, le=65535, description="DTU Modbus port")
    unit_id: int = Field(default=1, ge=1, le=255, description="Modbus unit ID")
    
    @field_validator('host')
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate host is not empty."""
        if not v or not v.strip():
            raise ValueError("DTU host cannot be empty")
        return v.strip()


class MqttConfig(BaseModel):
    """MQTT broker configuration."""

    broker: str = Field(..., description="MQTT broker address")
    port: int = Field(default=1883, ge=1, le=65535, description="MQTT broker port")
    user: Optional[str] = Field(default=None, description="MQTT username")
    password: Optional[str] = Field(default=None, description="MQTT password")
    password_file: Optional[Path] = Field(default=None, description="Path to file containing MQTT password")
    tls: bool = Field(default=False, description="Enable TLS")
    tls_insecure: bool = Field(default=False, description="Allow insecure TLS (do not use in production)")
    tls_ca_cert: Optional[Path] = Field(default=None, description="Path to CA certificate for TLS")
    client_id: str = Field(default="hoymiles-mqtt", description="MQTT client ID")
    keepalive: int = Field(default=60, ge=5, description="MQTT keepalive interval in seconds")
    qos: int = Field(default=1, ge=0, le=2, description="MQTT QoS level")
    topic_prefix: str = Field(default="homeassistant", description="MQTT topic prefix")
    
    @model_validator(mode='after')
    def load_password_from_file(self) -> 'MqttConfig':
        """Load password from file if password_file is specified."""
        if self.password_file and self.password_file.exists():
            self.password = self.password_file.read_text().strip()
        return self
    
    @field_validator('broker')
    @classmethod
    def validate_broker(cls, v: str) -> str:
        """Validate broker is not empty."""
        if not v or not v.strip():
            raise ValueError("MQTT broker cannot be empty")
        return v.strip()


class ModbusConfig(BaseModel):
    """Modbus communication parameters."""

    timeout: int = Field(default=3, ge=1, description="Request timeout in seconds")
    retries: int = Field(default=3, ge=0, description="Max retries per request")
    reconnect_delay: float = Field(default=0, ge=0, description="Minimum reconnect delay in seconds")
    reconnect_delay_max: float = Field(default=300, ge=0, description="Maximum reconnect delay in seconds")
    
    @model_validator(mode='after')
    def validate_reconnect_delays(self) -> 'ModbusConfig':
        """Validate reconnect delay settings."""
        if self.reconnect_delay > self.reconnect_delay_max:
            raise ValueError("reconnect_delay cannot be greater than reconnect_delay_max")
        return self


class EntityFilterConfig(BaseModel):
    """Entity filtering configuration."""

    mi_entities: List[str] = Field(
        default=[
            'grid_voltage',
            'grid_frequency',
            'temperature',
            'operating_status',
            'alarm_code',
            'alarm_count',
            'link_status',
        ],
        description="Microinverter entities to publish",
    )
    port_entities: List[str] = Field(
        default=['pv_voltage', 'pv_current', 'pv_power', 'today_production', 'total_production'],
        description="Port/panel entities to publish",
    )
    exclude_inverters: List[str] = Field(default=[], description="Inverter serial numbers to exclude")
    value_multipliers: Dict[str, float] = Field(default={}, description="Value multipliers for entities")
    entity_friendly_names: Dict[str, str] = Field(default={}, description="Custom friendly names for entities")


class TimingConfig(BaseModel):
    """Timing and scheduling configuration."""

    query_period: int = Field(default=60, ge=5, description="Query period in seconds")
    expire_after: int = Field(default=0, ge=0, description="Entity expiration time in seconds (0 = never)")
    reset_hour: int = Field(default=23, ge=0, le=23, description="Hour to reset daily production (0-23)")
    timezone: str = Field(default="UTC", description="Timezone for scheduling (e.g., 'America/New_York')")
    
    @model_validator(mode='after')
    def validate_expire_after(self) -> 'TimingConfig':
        """Validate expire_after is greater than query_period if set."""
        if self.expire_after > 0 and self.expire_after <= self.query_period:
            raise ValueError("expire_after must be greater than query_period when enabled")
        return self


class PersistenceConfig(BaseModel):
    """Data persistence configuration."""

    enabled: bool = Field(default=True, description="Enable data persistence")
    database_path: Path = Field(default=Path("/data/hoymiles-mqtt.db"), description="SQLite database path")
    backup_on_shutdown: bool = Field(default=True, description="Backup database on shutdown")


class HealthConfig(BaseModel):
    """Health check configuration."""

    enabled: bool = Field(default=True, description="Enable health check endpoint")
    host: str = Field(default="0.0.0.0", description="Health check server host")
    port: int = Field(default=8080, ge=1, le=65535, description="Health check server port")
    metrics_enabled: bool = Field(default=True, description="Enable Prometheus metrics")


class AlertsConfig(BaseModel):
    """Alerting configuration."""

    enabled: bool = Field(default=False, description="Enable alerts")
    dtu_offline_threshold: int = Field(default=300, ge=60, description="DTU offline threshold in seconds")
    temperature_threshold: float = Field(default=80.0, ge=0, description="Temperature warning threshold in Celsius")
    production_drop_threshold: float = Field(
        default=0.5, ge=0, le=1, description="Production drop threshold (0-1 ratio)"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="WARNING", description="Log level")
    format: str = Field(default="standard", description="Log format: standard or json")
    file: Optional[Path] = Field(default=None, description="Log file path")
    console: bool = Field(default=False, description="Log to console")
    max_bytes: int = Field(default=10485760, ge=1024, description="Max log file size in bytes")
    backup_count: int = Field(default=5, ge=0, description="Number of log file backups")
    
    @field_validator('level')
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v_upper


class ErrorRecoveryConfig(BaseModel):
    """Error recovery configuration."""

    exponential_backoff: bool = Field(default=True, description="Use exponential backoff for retries")
    max_backoff: int = Field(default=300, ge=1, description="Maximum backoff time in seconds")
    circuit_breaker_threshold: int = Field(default=5, ge=1, description="Failures before circuit breaker opens")
    circuit_breaker_timeout: int = Field(default=60, ge=1, description="Circuit breaker timeout in seconds")


class AppConfig(BaseSettings):
    """Main application configuration."""

    model_config = SettingsConfigDict(
        env_prefix='',
        env_nested_delimiter='__',
        case_sensitive=False,
        extra='ignore',
    )

    # Configuration file
    config_file: Optional[Path] = Field(default=None, description="Configuration file path")
    
    # DTU configuration - support for multiple DTUs
    dtu_host: Optional[str] = Field(default=None, description="Single DTU host (legacy)")
    dtu_port: int = Field(default=502, description="Single DTU port (legacy)")
    dtu_configs: List[DtuConfig] = Field(default=[], description="Multiple DTU configurations")
    microinverter_type: Optional[str] = Field(default=None, description="Microinverter type (e.g., 'HM', 'HMS', 'HMT')")
    
    # MQTT configuration
    mqtt_broker: Optional[str] = Field(default=None, description="MQTT broker address")
    mqtt_port: int = Field(default=1883, description="MQTT broker port")
    mqtt_user: Optional[str] = Field(default=None, description="MQTT username")
    mqtt_password: Optional[str] = Field(default=None, description="MQTT password")
    mqtt_password_file: Optional[str] = Field(default=None, description="MQTT password file")
    mqtt_tls: bool = Field(default=False, description="Enable MQTT TLS")
    mqtt_tls_insecure: bool = Field(default=False, description="MQTT TLS insecure")
    mqtt_tls_ca_cert: Optional[str] = Field(default=None, description="MQTT TLS CA certificate")
    mqtt_client_id: str = Field(default="hoymiles-mqtt", description="MQTT client ID")
    mqtt_topic_prefix: str = Field(default="homeassistant", description="MQTT topic prefix")
    
    # Modbus configuration
    modbus_unit_id: int = Field(default=1, description="Modbus unit ID")
    comm_timeout: int = Field(default=3, description="Modbus timeout")
    comm_retries: int = Field(default=3, description="Modbus retries")
    comm_reconnect_delay: float = Field(default=0, description="Modbus reconnect delay")
    comm_reconnect_delay_max: float = Field(default=300, description="Modbus max reconnect delay")
    
    # Entity filtering
    mi_entities: Optional[List[str]] = Field(default=None, description="Microinverter entities")
    port_entities: Optional[List[str]] = Field(default=None, description="Port entities")
    exclude_inverters: List[str] = Field(default=[], description="Exclude inverter serial numbers")
    value_multipliers: Dict[str, float] = Field(default={}, description="Value multipliers")
    entity_friendly_names: Dict[str, str] = Field(default={}, description="Entity friendly names")
    
    # Timing
    query_period: int = Field(default=60, description="Query period in seconds")
    expire_after: int = Field(default=0, description="Entity expiration time")
    reset_hour: int = Field(default=23, description="Daily reset hour")
    timezone: str = Field(default="UTC", description="Timezone")
    
    # Persistence
    persistence_enabled: bool = Field(default=True, description="Enable persistence")
    database_path: str = Field(default="/data/hoymiles-mqtt.db", description="Database path")
    
    # Health check
    health_enabled: bool = Field(default=True, description="Enable health check")
    health_host: str = Field(default="0.0.0.0", description="Health check host")
    health_port: int = Field(default=8080, description="Health check port")
    metrics_enabled: bool = Field(default=True, description="Enable metrics")
    
    # Alerts
    alerts_enabled: bool = Field(default=False, description="Enable alerts")
    dtu_offline_threshold: int = Field(default=300, description="DTU offline threshold")
    temperature_threshold: float = Field(default=80.0, description="Temperature threshold")
    
    # Logging
    log_level: str = Field(default="WARNING", description="Log level")
    log_format: str = Field(default="standard", description="Log format")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    log_to_console: bool = Field(default=False, description="Log to console")
    
    # Error recovery
    exponential_backoff: bool = Field(default=True, description="Use exponential backoff")
    circuit_breaker_threshold: int = Field(default=5, description="Circuit breaker threshold")
    
    # Advanced options
    dry_run: bool = Field(default=False, description="Dry run mode (no publishing)")
    dump_data: bool = Field(default=False, description="Dump raw data to file")
    dump_data_path: Optional[Path] = Field(default=None, description="Data dump file path")

    def get_mqtt_config(self) -> MqttConfig:
        """Get MQTT configuration object."""
        return MqttConfig(
            broker=self.mqtt_broker or "localhost",
            port=self.mqtt_port,
            user=self.mqtt_user,
            password=self.mqtt_password,
            password_file=Path(self.mqtt_password_file) if self.mqtt_password_file else None,
            tls=self.mqtt_tls,
            tls_insecure=self.mqtt_tls_insecure,
            tls_ca_cert=Path(self.mqtt_tls_ca_cert) if self.mqtt_tls_ca_cert else None,
            client_id=self.mqtt_client_id,
            topic_prefix=self.mqtt_topic_prefix,
        )
    
    def get_dtu_configs(self) -> List[DtuConfig]:
        """Get list of DTU configurations."""
        if self.dtu_configs:
            return self.dtu_configs
        elif self.dtu_host:
            # Legacy single DTU configuration
            return [DtuConfig(name="DTU", host=self.dtu_host, port=self.dtu_port, unit_id=self.modbus_unit_id)]
        else:
            raise ValueError("At least one DTU must be configured (dtu_host or dtu_configs)")
    
    def get_modbus_config(self) -> ModbusConfig:
        """Get Modbus configuration object."""
        return ModbusConfig(
            timeout=self.comm_timeout,
            retries=self.comm_retries,
            reconnect_delay=self.comm_reconnect_delay,
            reconnect_delay_max=self.comm_reconnect_delay_max,
        )
    
    def get_entity_filter_config(self) -> EntityFilterConfig:
        """Get entity filter configuration."""
        return EntityFilterConfig(
            mi_entities=self.mi_entities or [
                'grid_voltage',
                'grid_frequency',
                'temperature',
                'operating_status',
                'alarm_code',
                'alarm_count',
                'link_status',
            ],
            port_entities=self.port_entities or [
                'pv_voltage',
                'pv_current',
                'pv_power',
                'today_production',
                'total_production',
            ],
            exclude_inverters=self.exclude_inverters,
            value_multipliers=self.value_multipliers,
            entity_friendly_names=self.entity_friendly_names,
        )
    
    def get_timing_config(self) -> TimingConfig:
        """Get timing configuration."""
        return TimingConfig(
            query_period=self.query_period,
            expire_after=self.expire_after,
            reset_hour=self.reset_hour,
            timezone=self.timezone,
        )
    
    def get_persistence_config(self) -> PersistenceConfig:
        """Get persistence configuration."""
        return PersistenceConfig(
            enabled=self.persistence_enabled,
            database_path=Path(self.database_path),
        )
    
    def get_health_config(self) -> HealthConfig:
        """Get health check configuration."""
        return HealthConfig(
            enabled=self.health_enabled,
            host=self.health_host,
            port=self.health_port,
            metrics_enabled=self.metrics_enabled,
        )
    
    def get_logging_config(self) -> LoggingConfig:
        """Get logging configuration."""
        return LoggingConfig(
            level=self.log_level,
            format=self.log_format,
            file=Path(self.log_file) if self.log_file else None,
            console=self.log_to_console,
        )

    @model_validator(mode='after')
    def validate_config(self) -> 'AppConfig':
        """Validate complete configuration."""
        # Ensure at least one DTU is configured
        if not self.dtu_host and not self.dtu_configs:
            raise ValueError("At least one DTU must be configured")
        
        # Ensure MQTT broker is configured
        if not self.mqtt_broker:
            raise ValueError("MQTT broker must be configured")
        
        return self

