"""InfluxDB v3 client for pushing solar data to InfluxDB Cloud/IOx."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Try importing InfluxDB v3 client
try:
    from influxdb_client_3 import InfluxDBClient3, Point, WriteOptions
    HAS_INFLUXDB = True
except ImportError:
    HAS_INFLUXDB = False
    logger.warning("influxdb3-python not installed - InfluxDB support disabled")


class InfluxDBWriter:
    """Writer for pushing solar production data to InfluxDB v3."""

    def __init__(
        self,
        enabled: bool = False,
        host: Optional[str] = None,
        token: Optional[str] = None,
        database: Optional[str] = None,
        org: Optional[str] = None,
    ):
        """Initialize InfluxDB writer.
        
        Args:
            enabled: Whether InfluxDB is enabled
            host: InfluxDB host URL (e.g., https://influxdb3.example.com)
            token: InfluxDB API token
            database: InfluxDB database/bucket name
            org: InfluxDB organization (optional for v3)
        """
        self.enabled = enabled
        self.host = host
        self.token = token
        self.database = database
        self.org = org
        self.client: Optional[InfluxDBClient3] = None
        
        if not HAS_INFLUXDB and self.enabled:
            logger.error("InfluxDB enabled but influxdb3-python not installed")
            self.enabled = False
        
        if self.enabled:
            self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize InfluxDB client connection."""
        try:
            if not self.host or not self.token:
                logger.error("InfluxDB host and token are required")
                self.enabled = False
                return
            
            # Create InfluxDB v3 client
            self.client = InfluxDBClient3(
                host=self.host,
                token=self.token,
                database=self.database or "hoymiles",
                org=self.org,
            )
            
            logger.info(f"Connected to InfluxDB v3 at {self.host}")
            
        except Exception as e:
            logger.error(f"Failed to initialize InfluxDB client: {e}")
            self.enabled = False
    
    def write_dtu_data(
        self,
        dtu_name: str,
        dtu_serial: str,
        data: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Write DTU-level data to InfluxDB.
        
        Args:
            dtu_name: DTU name
            dtu_serial: DTU serial number
            data: Data dictionary with metrics
            timestamp: Optional timestamp (defaults to now)
        """
        if not self.enabled or not self.client:
            return
        
        try:
            ts = timestamp or datetime.now(timezone.utc)
            
            # Create point for DTU data
            point = Point("dtu") \
                .tag("dtu_name", dtu_name) \
                .tag("dtu_serial", dtu_serial) \
                .time(ts)
            
            # Add fields from data
            if "pv_power" in data:
                point.field("pv_power", float(data["pv_power"]))
            if "today_production" in data:
                point.field("today_production", int(data["today_production"]))
            if "total_production" in data:
                point.field("total_production", int(data["total_production"]))
            if "alarm_flag" in data:
                point.field("alarm_flag", data["alarm_flag"] == "ON")
            
            self.client.write(point)
            logger.debug(f"Wrote DTU data for {dtu_name} to InfluxDB")
            
        except Exception as e:
            logger.error(f"Failed to write DTU data to InfluxDB: {e}")
    
    def write_inverter_data(
        self,
        serial_number: str,
        dtu_name: str,
        data: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Write inverter data to InfluxDB.
        
        Args:
            serial_number: Inverter serial number
            dtu_name: DTU name
            data: Inverter data dictionary
            timestamp: Optional timestamp (defaults to now)
        """
        if not self.enabled or not self.client:
            return
        
        try:
            ts = timestamp or datetime.now(timezone.utc)
            
            # Create point for inverter
            point = Point("inverter") \
                .tag("serial_number", serial_number) \
                .tag("dtu_name", dtu_name) \
                .time(ts)
            
            # Add inverter fields
            if "grid_voltage" in data:
                point.field("grid_voltage", float(data["grid_voltage"]))
            if "grid_frequency" in data:
                point.field("grid_frequency", float(data["grid_frequency"]))
            if "temperature" in data:
                point.field("temperature", float(data["temperature"]))
            if "operating_status" in data:
                point.field("operating_status", int(data["operating_status"]))
            if "alarm_code" in data:
                point.field("alarm_code", int(data["alarm_code"]))
            if "alarm_count" in data:
                point.field("alarm_count", int(data["alarm_count"]))
            if "link_status" in data:
                point.field("link_status", int(data["link_status"]))
            
            self.client.write(point)
            logger.debug(f"Wrote inverter data for {serial_number} to InfluxDB")
            
        except Exception as e:
            logger.error(f"Failed to write inverter data to InfluxDB: {e}")
    
    def write_port_data(
        self,
        serial_number: str,
        port_number: int,
        dtu_name: str,
        data: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Write port/panel data to InfluxDB.
        
        Args:
            serial_number: Inverter serial number
            port_number: Port number
            dtu_name: DTU name
            data: Port data dictionary
            timestamp: Optional timestamp (defaults to now)
        """
        if not self.enabled or not self.client:
            return
        
        try:
            ts = timestamp or datetime.now(timezone.utc)
            
            # Create point for port
            point = Point("port") \
                .tag("serial_number", serial_number) \
                .tag("port_number", str(port_number)) \
                .tag("dtu_name", dtu_name) \
                .time(ts)
            
            # Add port fields
            if "pv_voltage" in data:
                point.field("pv_voltage", float(data["pv_voltage"]))
            if "pv_current" in data:
                point.field("pv_current", float(data["pv_current"]))
            if "pv_power" in data:
                point.field("pv_power", float(data["pv_power"]))
            if "today_production" in data:
                point.field("today_production", int(data["today_production"]))
            if "total_production" in data:
                point.field("total_production", int(data["total_production"]))
            
            self.client.write(point)
            logger.debug(f"Wrote port {port_number} data for {serial_number} to InfluxDB")
            
        except Exception as e:
            logger.error(f"Failed to write port data to InfluxDB: {e}")
    
    def write_batch(self, points: List[Point]) -> None:
        """Write multiple points in batch.
        
        Args:
            points: List of Point objects to write
        """
        if not self.enabled or not self.client or not points:
            return
        
        try:
            self.client.write(points)
            logger.debug(f"Wrote {len(points)} points to InfluxDB")
            
        except Exception as e:
            logger.error(f"Failed to write batch to InfluxDB: {e}")
    
    def query(self, query: str) -> Any:
        """Execute a query against InfluxDB.
        
        Args:
            query: SQL query to execute
            
        Returns:
            Query results
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            return self.client.query(query)
        except Exception as e:
            logger.error(f"Failed to query InfluxDB: {e}")
            return None
    
    def close(self) -> None:
        """Close InfluxDB client connection."""
        if self.client:
            try:
                self.client.close()
                logger.info("InfluxDB client closed")
            except Exception as e:
                logger.error(f"Error closing InfluxDB client: {e}")
            finally:
                self.client = None

