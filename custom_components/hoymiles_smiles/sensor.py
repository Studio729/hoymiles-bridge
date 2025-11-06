"""Sensor platform for Hoymiles S-Miles."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_TYPES, INVERTER_SENSOR_TYPES
from .coordinator import HoymilesMqttCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class HoymilesMqttSensorEntityDescription(SensorEntityDescription):
    """Describe Hoymiles S-Miles sensor entity."""

    value_fn: Callable[[HoymilesMqttCoordinator], StateType] = None
    attributes_fn: Callable[[HoymilesMqttCoordinator], dict[str, Any]] = None


SENSOR_DESCRIPTIONS: tuple[HoymilesMqttSensorEntityDescription, ...] = (
    HoymilesMqttSensorEntityDescription(
        key="uptime",
        name="Uptime",
        icon="mdi:clock-outline",
        native_unit_of_measurement="s",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda coordinator: (
            coordinator.get_health_data().get("uptime_seconds")
            if coordinator.get_health_data()
            else None
        ),
        attributes_fn=lambda coordinator: {
            "start_time": (
                coordinator.get_health_data().get("start_time")
                if coordinator.get_health_data()
                else None
            ),
        },
    ),
    HoymilesMqttSensorEntityDescription(
        key="messages_published",
        name="MQTT Messages Published",
        icon="mdi:message-arrow-right",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda coordinator: (
            coordinator.get_health_data().get("mqtt", {}).get("messages_published")
            if coordinator.get_health_data()
            else None
        ),
    ),
    HoymilesMqttSensorEntityDescription(
        key="mqtt_errors",
        name="MQTT Errors",
        icon="mdi:alert-circle-outline",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda coordinator: (
            coordinator.get_health_data().get("mqtt", {}).get("errors")
            if coordinator.get_health_data()
            else None
        ),
    ),
    HoymilesMqttSensorEntityDescription(
        key="dtu_query_count",
        name="DTU Query Count",
        icon="mdi:counter",
        native_unit_of_measurement="queries",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda coordinator: (
            coordinator.get_dtu_data().get("query_count")
            if coordinator.get_dtu_data()
            else None
        ),
        attributes_fn=lambda coordinator: {
            "dtu_status": (
                coordinator.get_dtu_data().get("status")
                if coordinator.get_dtu_data()
                else "unknown"
            ),
        },
    ),
    HoymilesMqttSensorEntityDescription(
        key="dtu_error_count",
        name="DTU Error Count",
        icon="mdi:alert-circle",
        native_unit_of_measurement="errors",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda coordinator: (
            coordinator.get_dtu_data().get("error_count")
            if coordinator.get_dtu_data()
            else None
        ),
        attributes_fn=lambda coordinator: {
            "last_error": (
                coordinator.get_dtu_data().get("last_error")
                if coordinator.get_dtu_data()
                else None
            ),
            "last_error_time": (
                coordinator.get_dtu_data().get("last_error_time")
                if coordinator.get_dtu_data()
                else None
            ),
        },
    ),
    HoymilesMqttSensorEntityDescription(
        key="dtu_last_query",
        name="DTU Last Query",
        icon="mdi:clock-check-outline",
        native_unit_of_measurement="s",
        device_class=SensorDeviceClass.DURATION,
        value_fn=lambda coordinator: (
            coordinator.get_dtu_data().get("seconds_since_last_success")
            if coordinator.get_dtu_data()
            else None
        ),
        attributes_fn=lambda coordinator: {
            "last_successful_query": (
                coordinator.get_dtu_data().get("last_successful_query")
                if coordinator.get_dtu_data()
                else None
            ),
        },
    ),
    HoymilesMqttSensorEntityDescription(
        key="database_size",
        name="Database Size",
        icon="mdi:database",
        native_unit_of_measurement="MB",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=2,
        value_fn=lambda coordinator: (
            round(coordinator.get_stats_data().get("database_size_bytes", 0) / 1024 / 1024, 2)
            if coordinator.get_stats_data()
            else None
        ),
    ),
    HoymilesMqttSensorEntityDescription(
        key="cached_records",
        name="Cached Records",
        icon="mdi:database-check",
        native_unit_of_measurement="records",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda coordinator: (
            coordinator.get_stats_data().get("total_records")
            if coordinator.get_stats_data()
            else None
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Hoymiles S-Miles sensors from config entry."""
    coordinator: HoymilesMqttCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create system-level sensors
    entities = [
        HoymilesMqttSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    ]

    # Create inverter sensors
    inverters = coordinator.get_inverters()
    _LOGGER.info("Setting up sensors for %d inverters", len(inverters))
    
    for inverter in inverters:
        serial_number = inverter.get("serial_number")
        if not serial_number:
            continue
        
        _LOGGER.debug("Creating sensors for inverter %s", serial_number)
        
        # Create sensors for this inverter
        for sensor_key in INVERTER_SENSOR_TYPES:
            entities.append(
                InverterSensor(
                    coordinator=coordinator,
                    entry=entry,
                    serial_number=serial_number,
                    sensor_key=sensor_key,
                    inverter_info=inverter,
                )
            )

    async_add_entities(entities)


class HoymilesMqttSensor(CoordinatorEntity[HoymilesMqttCoordinator], SensorEntity):
    """Representation of a Hoymiles S-Miles sensor."""

    entity_description: HoymilesMqttSensorEntityDescription

    def __init__(
        self,
        coordinator: HoymilesMqttCoordinator,
        entry: ConfigEntry,
        description: HoymilesMqttSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Hoymiles S-Miles",
            "manufacturer": "Hoymiles",
            "model": "S-Miles Bridge",
            "sw_version": "2.0.0",
        }

    async def async_added_to_hass(self) -> None:
        """Handle entity added to hass."""
        await super().async_added_to_hass()
        
        # Schedule initial state write after entity is fully registered
        # Add a small delay to ensure recorder is ready
        async def write_initial_state():
            """Write initial state after recorder is ready."""
            import asyncio
            # Wait a moment for recorder to fully register the entity
            await asyncio.sleep(0.5)
            
            _LOGGER.debug(
                "[Initial State] Writing initial state for %s sensor: %s (available=%s)",
                self.entity_description.name,
                self.native_value,
                self.available
            )
            self.async_write_ha_state()
            
            # Force another write after 1 second to be absolutely sure
            await asyncio.sleep(1)
            _LOGGER.debug("[Initial State] Writing second state for %s to ensure history capture", self.entity_description.name)
            self.async_write_ha_state()
        
        # Schedule for execution
        self.hass.async_create_task(write_initial_state())

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if self.entity_description.attributes_fn:
            return self.entity_description.attributes_fn(self.coordinator)
        return {}

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.is_available()


class InverterSensor(CoordinatorEntity[HoymilesMqttCoordinator], SensorEntity):
    """Representation of a Hoymiles inverter sensor."""

    def __init__(
        self,
        coordinator: HoymilesMqttCoordinator,
        entry: ConfigEntry,
        serial_number: str,
        sensor_key: str,
        inverter_info: dict[str, Any],
    ) -> None:
        """Initialize the inverter sensor."""
        super().__init__(coordinator)
        self._serial_number = serial_number
        self._sensor_key = sensor_key
        self._inverter_info = inverter_info
        self._attr_has_entity_name = True
        
        # Get sensor configuration
        sensor_config = INVERTER_SENSOR_TYPES[sensor_key]
        
        # Set unique ID
        self._attr_unique_id = f"{entry.entry_id}_{serial_number}_{sensor_key}"
        
        # Set entity attributes from sensor configuration
        self._attr_name = sensor_config["name"]
        self._attr_icon = sensor_config["icon"]
        self._attr_native_unit_of_measurement = sensor_config.get("unit")
        
        # Device class
        if sensor_config.get("device_class"):
            self._attr_device_class = SensorDeviceClass(sensor_config["device_class"])
        
        # State class
        if sensor_config.get("state_class"):
            self._attr_state_class = SensorStateClass(sensor_config["state_class"])
        
        # Entity category
        if sensor_config.get("entity_category"):
            self._attr_entity_category = EntityCategory(sensor_config["entity_category"])
        
        # Device info - create a device for each inverter
        self._attr_device_info = {
            "identifiers": {(DOMAIN, serial_number)},
            "name": f"Inverter {serial_number}",
            "manufacturer": "Hoymiles",
            "model": inverter_info.get("inverter_type", "Unknown"),
            "via_device": (DOMAIN, entry.entry_id),
        }
        
        # Cache for latest data
        self._latest_data: dict[str, Any] | None = None

    async def async_added_to_hass(self) -> None:
        """Handle entity added to hass."""
        await super().async_added_to_hass()
        
        # Fetch initial detailed data for this inverter
        self._latest_data = await self.coordinator.get_inverter_latest_data(self._serial_number)
        
        # Schedule initial state write
        async def write_initial_state():
            """Write initial state after recorder is ready."""
            import asyncio
            await asyncio.sleep(0.5)
            
            _LOGGER.debug(
                "[Initial State] Writing initial state for inverter %s sensor %s: %s",
                self._serial_number, self._sensor_key, self.native_value
            )
            self.async_write_ha_state()
            
            await asyncio.sleep(1)
            self.async_write_ha_state()
        
        self.hass.async_create_task(write_initial_state())

    async def async_update(self) -> None:
        """Update the entity."""
        await super().async_update()
        # Fetch latest detailed data for this inverter
        self._latest_data = await self.coordinator.get_inverter_latest_data(self._serial_number)

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self._latest_data:
            return None
        
        raw_data = self._latest_data.get("raw_data", {})
        ports = self._latest_data.get("ports", [])
        
        # Map sensor keys to data fields
        if self._sensor_key == "pv_power":
            # Sum power across all ports
            if ports:
                total_power = sum(port.get("pv_power", 0) or 0 for port in ports)
                return round(total_power, 2) if total_power else 0
            return self._latest_data.get("pv_power", 0)
        
        elif self._sensor_key == "pv_voltage":
            # Get voltage from first port (typically all ports have same voltage)
            if ports and len(ports) > 0:
                return round(ports[0].get("pv_voltage", 0) or 0, 2)
            return self._latest_data.get("pv_voltage")
        
        elif self._sensor_key == "pv_current":
            # Sum current across all ports
            if ports:
                total_current = sum(port.get("pv_current", 0) or 0 for port in ports)
                return round(total_current, 3) if total_current else 0
            return self._latest_data.get("pv_current")
        
        elif self._sensor_key == "grid_voltage":
            value = self._latest_data.get("grid_voltage")
            return round(value, 2) if value else None
        
        elif self._sensor_key == "grid_frequency":
            value = self._latest_data.get("grid_frequency")
            return round(value, 2) if value else None
        
        elif self._sensor_key == "temperature":
            value = self._latest_data.get("temperature")
            return round(value, 1) if value else None
        
        elif self._sensor_key == "today_production":
            # Sum today's production across all ports
            if ports:
                total = sum(port.get("today_production", 0) or 0 for port in ports)
                return int(total) if total else 0
            return raw_data.get("today_production", 0)
        
        elif self._sensor_key == "total_production":
            # Sum total production across all ports and convert to kWh
            if ports:
                total = sum(port.get("total_production", 0) or 0 for port in ports)
                return round(total / 1000, 2) if total else 0  # Convert Wh to kWh
            return round(raw_data.get("total_production", 0) / 1000, 2)
        
        elif self._sensor_key == "operating_status":
            return self._latest_data.get("operating_status")
        
        elif self._sensor_key == "link_status":
            return self._latest_data.get("link_status")
        
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self._latest_data:
            return {}
        
        attributes = {
            "serial_number": self._serial_number,
            "dtu_name": self._inverter_info.get("dtu_name"),
            "last_seen": self._latest_data.get("timestamp"),
        }
        
        # Add port-specific information
        ports = self._latest_data.get("ports", [])
        if ports:
            attributes["port_count"] = len(ports)
            # Add per-port details for power-related sensors
            if self._sensor_key in ["pv_power", "pv_current", "today_production", "total_production"]:
                for idx, port in enumerate(ports, 1):
                    if self._sensor_key == "pv_power":
                        attributes[f"port_{idx}_power"] = port.get("pv_power", 0)
                    elif self._sensor_key == "pv_current":
                        attributes[f"port_{idx}_current"] = port.get("pv_current", 0)
                    elif self._sensor_key == "today_production":
                        attributes[f"port_{idx}_today"] = port.get("today_production", 0)
                    elif self._sensor_key == "total_production":
                        attributes[f"port_{idx}_total_kwh"] = round(port.get("total_production", 0) / 1000, 2)
        
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success 
            and self.coordinator.is_available()
            and self._latest_data is not None
        )

