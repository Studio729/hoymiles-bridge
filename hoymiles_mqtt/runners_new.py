"""Enhanced runners with multi-DTU support and better error handling."""

import logging
import signal
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import pytz
from hoymiles_modbus.client import HoymilesModbusTCP
from pymodbus import exceptions as pymodbus_exceptions

from hoymiles_mqtt.circuit_breaker import ErrorRecoveryManager
from hoymiles_mqtt.config import AppConfig, DtuConfig
from hoymiles_mqtt.ha import HassMqtt
from hoymiles_mqtt.health import HealthMetrics
from hoymiles_mqtt.mqtt_client import EnhancedMqttClient
from hoymiles_mqtt.persistence import PersistenceManager

logger = logging.getLogger(__name__)


class DtuQueryJob:
    """Query job for a single DTU."""
    
    def __init__(
        self,
        dtu_config: DtuConfig,
        mqtt_builder: HassMqtt,
        mqtt_client: EnhancedMqttClient,
        modbus_client: HoymilesModbusTCP,
        health_metrics: HealthMetrics,
        error_recovery: ErrorRecoveryManager,
        config: AppConfig,
    ):
        """Initialize DTU query job.
        
        Args:
            dtu_config: DTU configuration
            mqtt_builder: MQTT message builder
            mqtt_client: MQTT client
            modbus_client: Modbus client
            health_metrics: Health metrics tracker
            error_recovery: Error recovery manager
            config: Application configuration
        """
        self.dtu_config = dtu_config
        self.mqtt_builder = mqtt_builder
        self.mqtt_client = mqtt_client
        self.modbus_client = modbus_client
        self.health_metrics = health_metrics
        self.error_recovery = error_recovery
        self.config = config
        self.mqtt_configured = False
        self._lock = threading.Lock()
    
    def execute(self) -> bool:
        """Execute query job.
        
        Returns:
            True if successful
        """
        is_acquired = self._lock.acquire(blocking=False)
        if not is_acquired:
            logger.warning(
                f"Previous query for {self.dtu_config.name} not finished. "
                f"Query period may be too small."
            )
            return False
        
        try:
            start_time = time.time()
            
            # Query DTU through circuit breaker
            plant_data = self.error_recovery.execute_with_recovery(
                f"dtu_{self.dtu_config.name}",
                self._query_dtu,
            )
            
            if plant_data is None:
                # Circuit breaker is open or query failed
                circuit_breaker = self.error_recovery.get_circuit_breaker(f"dtu_{self.dtu_config.name}")
                self.health_metrics.update_circuit_breaker_state(
                    self.dtu_config.name,
                    circuit_breaker.is_open()
                )
                return False
            
            duration = time.time() - start_time
            self.health_metrics.record_query_success(self.dtu_config.name, duration)
            
            # Update circuit breaker state
            self.health_metrics.update_circuit_breaker_state(self.dtu_config.name, False)
            
            # Dump data if requested
            if self.config.dump_data:
                self._dump_plant_data(plant_data)
            
            # Publish to MQTT
            if not self.config.dry_run:
                self._publish_to_mqtt(plant_data)
            else:
                logger.info(f"[DRY RUN] Would publish {self.dtu_config.name} data")
            
            # Update metrics
            self._update_metrics(plant_data)
            
            return True
            
        except Exception as e:
            logger.exception(f"Unexpected error in query job for {self.dtu_config.name}: {e}")
            self.health_metrics.record_query_error(
                self.dtu_config.name,
                "unexpected",
                str(e)
            )
            return False
        finally:
            self._lock.release()
    
    def _query_dtu(self):
        """Query DTU for plant data."""
        logger.debug(f"Querying DTU {self.dtu_config.name} at {self.dtu_config.host}")
        return self.modbus_client.plant_data
    
    def _dump_plant_data(self, plant_data: Any) -> None:
        """Dump plant data to file."""
        if not self.config.dump_data_path:
            return
        
        try:
            import json
            from pathlib import Path
            
            dump_file = Path(self.config.dump_data_path)
            dump_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to dict (simplified)
            data_dict = {
                'timestamp': datetime.now().isoformat(),
                'dtu': self.dtu_config.name,
                'dtu_serial': plant_data.dtu,
                'pv_power': plant_data.pv_power,
                'today_production': plant_data.today_production,
                'total_production': plant_data.total_production,
                'inverters': [
                    {
                        'serial_number': inv.serial_number,
                        'port_number': inv.port_number,
                        'pv_voltage': inv.pv_voltage,
                        'pv_current': inv.pv_current,
                        'pv_power': inv.pv_power,
                        'grid_voltage': inv.grid_voltage,
                        'grid_frequency': inv.grid_frequency,
                        'temperature': inv.temperature,
                        'operating_status': inv.operating_status,
                    }
                    for inv in plant_data.inverters
                ],
            }
            
            with open(dump_file, 'a') as f:
                f.write(json.dumps(data_dict) + '\n')
            
        except Exception as e:
            logger.error(f"Failed to dump plant data: {e}")
    
    def _publish_to_mqtt(self, plant_data: Any) -> None:
        """Publish plant data to MQTT."""
        try:
            publish_count = 0
            
            # Publish configurations (first time only)
            if not self.mqtt_configured:
                for topic, payload in self.mqtt_builder.get_configs(plant_data=plant_data):
                    self.mqtt_client.publish(topic=topic, payload=payload, retain=True)
                    self.health_metrics.record_mqtt_publish('config')
                    publish_count += 1
                
                self.mqtt_configured = True
                logger.info(f"Published {publish_count} config messages for {self.dtu_config.name}")
                publish_count = 0
            
            # Publish state data
            for topic, payload in self.mqtt_builder.get_states(plant_data=plant_data):
                self.mqtt_client.publish(topic=topic, payload=payload)
                self.health_metrics.record_mqtt_publish('state')
                publish_count += 1
            
            logger.info(
                f"Queued {publish_count} state messages for {self.dtu_config.name}"
            )
            
        except Exception as e:
            logger.exception(f"Failed to publish data for {self.dtu_config.name}: {e}")
            self.health_metrics.record_mqtt_error('publish_failed')
    
    def _update_metrics(self, plant_data: Any) -> None:
        """Update Prometheus metrics."""
        try:
            # Update DTU metrics
            self.health_metrics.update_dtu_metrics(
                self.dtu_config.name,
                plant_data.pv_power,
                plant_data.today_production,
                plant_data.total_production,
            )
            
            # Update inverter metrics
            for inverter in plant_data.inverters:
                self.health_metrics.update_inverter_metrics(
                    inverter.serial_number,
                    inverter.port_number,
                    inverter.pv_power,
                    inverter.temperature,
                    inverter.operating_status,
                )
        
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")


class MultiDtuCoordinator:
    """Coordinates queries across multiple DTUs."""
    
    def __init__(
        self,
        config: AppConfig,
        mqtt_client: EnhancedMqttClient,
        persistence_manager: PersistenceManager,
        health_metrics: HealthMetrics,
        error_recovery: ErrorRecoveryManager,
    ):
        """Initialize multi-DTU coordinator.
        
        Args:
            config: Application configuration
            mqtt_client: MQTT client
            persistence_manager: Persistence manager
            health_metrics: Health metrics tracker
            error_recovery: Error recovery manager
        """
        self.config = config
        self.mqtt_client = mqtt_client
        self.persistence_manager = persistence_manager
        self.health_metrics = health_metrics
        self.error_recovery = error_recovery
        self.dtu_jobs: List[DtuQueryJob] = []
        self.timezone = pytz.timezone(config.timezone)
        self.last_reset_date: Optional[int] = None
        
        self._initialize_dtu_jobs()
    
    def _initialize_dtu_jobs(self) -> None:
        """Initialize query jobs for all DTUs."""
        dtu_configs = self.config.get_dtu_configs()
        modbus_config = self.config.get_modbus_config()
        entity_filter = self.config.get_entity_filter_config()
        timing_config = self.config.get_timing_config()
        
        for dtu_config in dtu_configs:
            # Create Modbus client for this DTU
            modbus_client = HoymilesModbusTCP(
                host=dtu_config.host,
                port=dtu_config.port,
                unit_id=dtu_config.unit_id,
            )
            modbus_client.comm_params.timeout = modbus_config.timeout
            modbus_client.comm_params.retries = modbus_config.retries
            modbus_client.comm_params.reconnect_delay = modbus_config.reconnect_delay
            modbus_client.comm_params.reconnect_delay_max = modbus_config.reconnect_delay_max
            
            # Create MQTT builder for this DTU
            mqtt_builder = HassMqtt(
                mi_entities=entity_filter.mi_entities,
                port_entities=entity_filter.port_entities,
                expire_after=timing_config.expire_after,
                exclude_inverters=entity_filter.exclude_inverters,
                value_multipliers=entity_filter.value_multipliers,
                entity_friendly_names=entity_filter.entity_friendly_names,
                persistence_manager=self.persistence_manager,
                topic_prefix=self.config.mqtt_topic_prefix,
                dtu_name=dtu_config.name,
            )
            
            # Create query job
            job = DtuQueryJob(
                dtu_config=dtu_config,
                mqtt_builder=mqtt_builder,
                mqtt_client=self.mqtt_client,
                modbus_client=modbus_client,
                health_metrics=self.health_metrics,
                error_recovery=self.error_recovery,
                config=self.config,
            )
            
            self.dtu_jobs.append(job)
            logger.info(f"Initialized query job for DTU {dtu_config.name} at {dtu_config.host}")
    
    def execute_all(self) -> None:
        """Execute queries for all DTUs."""
        # Check if we need to reset daily production
        self._check_daily_reset()
        
        # Execute all DTU queries (can be parallelized if needed)
        threads = []
        for job in self.dtu_jobs:
            thread = threading.Thread(target=job.execute)
            thread.start()
            threads.append(thread)
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
    
    def _check_daily_reset(self) -> None:
        """Check if daily production should be reset."""
        now = datetime.now(self.timezone)
        current_date = now.day
        
        # Check if it's the reset hour and we haven't reset today
        if now.hour == self.config.reset_hour and self.last_reset_date != current_date:
            logger.info(f"Daily reset triggered at {now.isoformat()}")
            
            # Reset all MQTT builders
            for job in self.dtu_jobs:
                job.mqtt_builder.clear_production_today()
            
            self.last_reset_date = current_date


def run_periodic_coordinator(
    coordinator: MultiDtuCoordinator,
    period: int,
    stop_event: threading.Event,
) -> None:
    """Run coordinator periodically.
    
    Args:
        coordinator: DTU coordinator
        period: Query period in seconds
        stop_event: Event to signal shutdown
    """
    logger.info(f"Starting periodic execution every {period} seconds")
    
    while not stop_event.is_set():
        try:
            coordinator.execute_all()
        except Exception as e:
            logger.exception(f"Error in coordinator execution: {e}")
        
        # Wait for next period or stop event
        if stop_event.wait(timeout=period):
            break
    
    logger.info("Periodic execution stopped")


def setup_signal_handlers(stop_event: threading.Event) -> None:
    """Setup signal handlers for graceful shutdown.
    
    Args:
        stop_event: Event to signal shutdown
    """
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        stop_event.set()
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

