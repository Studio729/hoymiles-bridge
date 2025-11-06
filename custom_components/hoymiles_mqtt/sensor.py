"""Sensor platform for Hoymiles MQTT Bridge."""
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

from .const import DOMAIN, SENSOR_TYPES
from .coordinator import HoymilesMqttCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class HoymilesMqttSensorEntityDescription(SensorEntityDescription):
    """Describe Hoymiles MQTT sensor entity."""

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
    """Set up Hoymiles MQTT sensors from config entry."""
    coordinator: HoymilesMqttCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        HoymilesMqttSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    ]

    async_add_entities(entities)


class HoymilesMqttSensor(CoordinatorEntity[HoymilesMqttCoordinator], SensorEntity):
    """Representation of a Hoymiles MQTT sensor."""

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
            "name": "Hoymiles MQTT Bridge",
            "manufacturer": "Hoymiles",
            "model": "MQTT Bridge",
            "sw_version": "1.1.7",
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

