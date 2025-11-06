"""MQTT message builders for Home Assistant."""

import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Optional, Tuple

if TYPE_CHECKING:
    from hoymiles_modbus.datatypes import PlantData
    from hoymiles_smiles.persistence import PersistenceManager

logger = logging.getLogger(__name__)

PLATFORM_SENSOR = 'sensor'
PLATFORM_BINARY_SENSOR = 'binary_sensor'

DEVICE_CLASS_VOLTAGE = 'voltage'
DEVICE_CLASS_CURRENT = 'current'
DEVICE_CLASS_FREQUENCY = 'frequency'
DEVICE_CLASS_POWER = 'power'
DEVICE_CLASS_ENERGY = 'energy'
DEVICE_CLASS_TEMPERATURE = 'temperature'
DEVICE_CLASS_PROBLEM = 'problem'

STATE_CLASS_MEASUREMENT = 'measurement'
STATE_CLASS_TOTAL_INCREASING = 'total_increasing'

UNIT_VOLTS = 'V'
UNIT_AMPERES = 'A'
UNIT_HERTZ = 'Hz'
UNIT_CELSIUS = '°C'
UNIT_WATS = 'W'
UNIT_WATS_PER_HOUR = 'Wh'

ZERO = 0


def _ignore_when_zero(data, entity_name):
    return getattr(data, entity_name) == ZERO


def _ignore_when_zero_operating_status(data, _):
    return _ignore_when_zero(data, 'operating_status')


@dataclass
class EntityDescription:
    """Common entity properties."""

    platform: str = PLATFORM_SENSOR
    device_class: Optional[str] = None
    unit: Optional[str] = None
    state_class: Optional[str] = None
    ignore_rule: Optional[Callable] = None
    expire: Optional[bool] = True
    value_converter: Optional[Callable] = None


MicroinverterEntities = {
    'grid_voltage': EntityDescription(
        device_class=DEVICE_CLASS_VOLTAGE,
        unit=UNIT_VOLTS,
        state_class=STATE_CLASS_MEASUREMENT,
        value_converter=float,
        ignore_rule=_ignore_when_zero_operating_status,
    ),
    'grid_frequency': EntityDescription(
        device_class=DEVICE_CLASS_FREQUENCY,
        unit=UNIT_HERTZ,
        state_class=STATE_CLASS_MEASUREMENT,
        value_converter=float,
        ignore_rule=_ignore_when_zero_operating_status,
    ),
    'temperature': EntityDescription(
        device_class=DEVICE_CLASS_TEMPERATURE,
        unit=UNIT_CELSIUS,
        state_class=STATE_CLASS_MEASUREMENT,
        value_converter=float,
        ignore_rule=_ignore_when_zero_operating_status,
    ),
    'operating_status': EntityDescription(),
    'alarm_code': EntityDescription(),
    'alarm_count': EntityDescription(),
    'link_status': EntityDescription(),
}

PortEntities = {
    'pv_voltage': EntityDescription(
        device_class=DEVICE_CLASS_VOLTAGE,
        unit=UNIT_VOLTS,
        state_class=STATE_CLASS_MEASUREMENT,
        value_converter=float,
        ignore_rule=_ignore_when_zero_operating_status,
    ),
    'pv_current': EntityDescription(
        device_class=DEVICE_CLASS_CURRENT,
        unit=UNIT_AMPERES,
        state_class=STATE_CLASS_MEASUREMENT,
        value_converter=float,
        ignore_rule=_ignore_when_zero_operating_status,
    ),
    'pv_power': EntityDescription(
        device_class=DEVICE_CLASS_POWER,
        unit=UNIT_WATS,
        state_class=STATE_CLASS_MEASUREMENT,
        value_converter=float,
        ignore_rule=_ignore_when_zero_operating_status,
    ),
    'today_production': EntityDescription(
        device_class=DEVICE_CLASS_ENERGY,
        unit=UNIT_WATS_PER_HOUR,
        state_class=STATE_CLASS_TOTAL_INCREASING,
        expire=False,
    ),
    'total_production': EntityDescription(
        device_class=DEVICE_CLASS_ENERGY,
        unit=UNIT_WATS_PER_HOUR,
        state_class=STATE_CLASS_TOTAL_INCREASING,
        expire=False,
    ),
}

DtuEntities = {
    'pv_power': EntityDescription(
        device_class=DEVICE_CLASS_POWER, unit=UNIT_WATS, state_class=STATE_CLASS_MEASUREMENT, value_converter=float
    ),
    'today_production': EntityDescription(
        device_class=DEVICE_CLASS_ENERGY,
        unit=UNIT_WATS_PER_HOUR,
        state_class=STATE_CLASS_TOTAL_INCREASING,
        ignore_rule=_ignore_when_zero,
        expire=False,
    ),
    'total_production': EntityDescription(
        device_class=DEVICE_CLASS_ENERGY,
        unit=UNIT_WATS_PER_HOUR,
        state_class=STATE_CLASS_TOTAL_INCREASING,
        ignore_rule=_ignore_when_zero,
        expire=False,
    ),
    'alarm_flag': EntityDescription(
        platform=PLATFORM_BINARY_SENSOR,
        device_class=DEVICE_CLASS_PROBLEM,
        value_converter=lambda x: 'ON' if x else 'OFF',
    ),
}


class HassMqtt:
    """MQTT message builder for Home Assistant."""

    def __init__(
        self,
        mi_entities: List[str],
        port_entities: List[str],
        post_process: bool = True,
        expire_after: int = 0,
        exclude_inverters: Optional[List[str]] = None,
        value_multipliers: Optional[Dict[str, float]] = None,
        entity_friendly_names: Optional[Dict[str, str]] = None,
        persistence_manager: Optional['PersistenceManager'] = None,
        topic_prefix: str = "homeassistant",
        dtu_name: str = "DTU",
    ) -> None:
        """Initialize the object.

        Arguments:
            mi_entities: names of microinverter entities that shall be handled by the builder
            port_entities: names of microinverter port entities that shall be handled by the builder
            post_process: if to cache energy production
            expire_after: number of seconds after which an entity state should expire
            exclude_inverters: serial numbers of inverters to exclude
            value_multipliers: multipliers to apply to entity values
            entity_friendly_names: custom friendly names for entities
            persistence_manager: optional persistence manager for cache storage
            topic_prefix: MQTT topic prefix
            dtu_name: friendly name for the DTU

        """
        self._logger = logger
        self._state_topics: Dict = {}
        self._config_topics: Dict = {}
        self._post_process: bool = post_process
        self._expire_after: int = expire_after
        self._prod_today_cache: Dict[Tuple[str, int], int] = {}
        self._prod_total_cache: Dict[Tuple[str, int], int] = {}
        self._mi_entities: Dict[str, EntityDescription] = {}
        self._port_entities: Dict[str, EntityDescription] = {}
        self._exclude_inverters = exclude_inverters or []
        self._value_multipliers = value_multipliers or {}
        self._entity_friendly_names = entity_friendly_names or {}
        self._persistence_manager = persistence_manager
        self._topic_prefix = topic_prefix
        self._dtu_name = dtu_name
        
        for entity_name, description in MicroinverterEntities.items():
            if entity_name in mi_entities:
                self._mi_entities[entity_name] = description
        for entity_name, description in PortEntities.items():
            if entity_name in port_entities:
                self._port_entities[entity_name] = description
        
        # Load cache from persistence if available
        if self._persistence_manager:
            self._load_cache_from_persistence()

    def _load_cache_from_persistence(self) -> None:
        """Load production cache from persistence."""
        if not self._persistence_manager:
            return
        
        cache = self._persistence_manager.load_production_cache()
        for (serial_number, port_number), (today_prod, total_prod) in cache.items():
            key = (serial_number, port_number)
            self._prod_today_cache[key] = today_prod
            self._prod_total_cache[key] = total_prod
        
        self._logger.info(f"Loaded production cache from persistence: {len(cache)} entries")
    
    def _save_cache_to_persistence(self) -> None:
        """Save production cache to persistence."""
        if not self._persistence_manager:
            return
        
        for (serial_number, port_number), today_prod in self._prod_today_cache.items():
            total_prod = self._prod_total_cache.get((serial_number, port_number), 0)
            self._persistence_manager.save_production_cache(
                serial_number, port_number, today_prod, total_prod
            )
    
    def _apply_value_multiplier(self, entity_name: str, value: Any) -> Any:
        """Apply value multiplier if configured.
        
        Args:
            entity_name: Entity name
            value: Original value
            
        Returns:
            Multiplied value or original value
        """
        if entity_name in self._value_multipliers and isinstance(value, (int, float)):
            return value * self._value_multipliers[entity_name]
        return value
    
    def _get_config_topic(self, platform: str, device_serial: str, entity_name: str) -> str:
        """Get configuration topic."""
        return f"{self._topic_prefix}/{platform}/{device_serial}/{entity_name}/config"

    def _get_state_topic(self, device_serial: str, port: Optional[int]) -> str:
        """Get state topic."""
        if port is not None:
            sub_topic = f'{device_serial}/{port}'
        else:
            sub_topic = device_serial
        return f"{self._topic_prefix}/hoymiles_smiles/{sub_topic}/state"

    def _get_config_payloads(
        self,
        device_name: str,
        device_serial_number,
        entity_definitions: Dict[str, EntityDescription],
        port: Optional[int] = None,
    ) -> Iterable[Tuple[str, str]]:
        port_prefix = f'port_{port}' if port is not None else ''
        entity_prefix = port_prefix if port_prefix else device_name
        for entity_name, entity_definition in entity_definitions.items():
            state_topic = self._get_state_topic(device_serial_number, port)
            config_payload = {
                "device": {
                    "name": f"{device_name}_{device_serial_number}",
                    "identifiers": [f"hoymiles_smiles_{device_serial_number}"],
                    "manufacturer": "Hoymiles",
                },
                "name": f'{port_prefix}_{entity_name}' if port_prefix else entity_name,
                "unique_id": f"hoymiles_smiles_{entity_prefix}_{device_serial_number}_{entity_name}",
                "state_topic": state_topic,
                "value_template": f"{{{{ iif(value_json.{entity_name} is defined, value_json.{entity_name}, '') }}}}",
                "availability_topic": state_topic,
                "availability_template": f"{{{{ iif(value_json.{entity_name} is defined, 'online', 'offline') }}}}",
            }
            if entity_definition.device_class:
                config_payload['device_class'] = entity_definition.device_class
            if entity_definition.unit:
                config_payload['unit_of_measurement'] = entity_definition.unit
            if entity_definition.state_class:
                config_payload['state_class'] = entity_definition.state_class
            if entity_definition.expire and self._expire_after:
                config_payload['expire_after'] = str(self._expire_after)
            config_topic = self._get_config_topic(
                entity_definition.platform, device_serial_number, f'{entity_prefix}_{entity_name}'
            )
            yield config_topic, json.dumps(config_payload)

    def clear_production_today(self) -> None:
        """Clear todays' energy production."""
        self._logger.debug('Clear today production cache.')
        self._prod_today_cache = {}
        
        # Clear in persistence as well
        if self._persistence_manager:
            self._persistence_manager.clear_today_production()

    def get_configs(self, plant_data: 'PlantData') -> Iterable[Tuple[str, str]]:
        """Get MQTT config messages for given data from DTU.

        Arguments:
            plant_data: data from DTU

        """
        for topic, payload in self._get_config_payloads('DTU', plant_data.dtu, DtuEntities):
            yield topic, payload
        for microinverter_data in plant_data.inverters:
            for topic, payload in self._get_config_payloads('inv', microinverter_data.serial_number, self._mi_entities):
                yield topic, payload
            for topic, payload in self._get_config_payloads(
                'inv',
                microinverter_data.serial_number,
                self._port_entities,
                microinverter_data.port_number,
            ):
                yield topic, payload

    def _get_state(
        self,
        device_serial: str,
        entity_definitions: Dict[str, EntityDescription],
        entity_data,
        port: Optional[int] = None,
    ) -> Tuple[str, str]:
        values = {}
        for entity_name, description in entity_definitions.items():
            value = getattr(entity_data, entity_name)
            if description.ignore_rule and description.ignore_rule(entity_data, entity_name):
                continue
            if description.value_converter:
                value = description.value_converter(value)
            # Apply value multiplier
            value = self._apply_value_multiplier(entity_name, value)
            values[entity_name] = value
        payload = json.dumps(values)
        state_topic = self._get_state_topic(device_serial, port)
        return state_topic, payload

    def _update_cache(self, plant_data: 'PlantData') -> None:
        for microinverter in plant_data.inverters:
            cache_key = (microinverter.serial_number, microinverter.port_number)
            if cache_key not in self._prod_today_cache:
                self._prod_today_cache[cache_key] = ZERO
            if cache_key not in self._prod_total_cache:
                self._prod_total_cache[cache_key] = ZERO
            if microinverter.operating_status > 0:
                if microinverter.today_production >= self._prod_today_cache[cache_key]:
                    self._prod_today_cache[cache_key] = microinverter.today_production
                else:
                    self._logger.warning(
                        f'Today production for {microinverter.serial_number} port {microinverter.port_number} '
                        f'is smaller ({microinverter.today_production} than cache '
                        f'({self._prod_today_cache[cache_key]}). '
                        f'Ignoring the fault value.'
                    )
                    microinverter.today_production = self._prod_today_cache[cache_key]
                if microinverter.total_production >= self._prod_total_cache[cache_key]:
                    self._prod_total_cache[cache_key] = microinverter.total_production
                else:
                    self._logger.warning(
                        f'Total production for {microinverter.serial_number} port {microinverter.port_number} '
                        f'is smaller ({microinverter.total_production} than cache '
                        f'({self._prod_total_cache[cache_key]}). '
                        f'Ignoring the fault value.'
                    )
                    microinverter.total_production = self._prod_total_cache[cache_key]

    def _process_plant_data(self, plant_data: 'PlantData') -> None:
        self._update_cache(plant_data)
        plant_data.today_production = sum(self._prod_today_cache.values()) if self._prod_today_cache else ZERO
        plant_data.total_production = sum(self._prod_total_cache.values()) if self._prod_total_cache else ZERO

    def get_states(self, plant_data: 'PlantData') -> Iterable[Tuple[str, str]]:
        """Get MQTT message for DTU data.

        Arguments:
            plant_data: data from DTU

        """
        if self._post_process:
            self._process_plant_data(plant_data)
        
        # Save cache to persistence after processing
        self._save_cache_to_persistence()
        
        yield self._get_state(plant_data.dtu, DtuEntities, plant_data)
        known_serials = []
        for microinverter_data in plant_data.inverters:
            # Skip excluded inverters
            if microinverter_data.serial_number in self._exclude_inverters:
                self._logger.debug(f"Skipping excluded inverter {microinverter_data.serial_number}")
                continue
            
            if microinverter_data.serial_number not in known_serials:
                known_serials.append(microinverter_data.serial_number)
                yield self._get_state(microinverter_data.serial_number, self._mi_entities, microinverter_data)
            yield self._get_state(
                microinverter_data.serial_number,
                self._port_entities,
                microinverter_data,
                microinverter_data.port_number,
            )
