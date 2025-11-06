"""Data persistence layer for caching production values."""

import json
import logging
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class PersistenceManager:
    """Manages persistent storage of production data."""

    def __init__(self, database_path: Path, enabled: bool = True):
        """Initialize persistence manager.
        
        Args:
            database_path: Path to SQLite database file
            enabled: Whether persistence is enabled
        """
        self.database_path = database_path
        self.enabled = enabled
        self.connection: Optional[sqlite3.Connection] = None
        
        if self.enabled:
            self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize database schema."""
        try:
            # Ensure directory exists
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.connection = sqlite3.connect(str(self.database_path), check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            
            cursor = self.connection.cursor()
            
            # Production cache table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS production_cache (
                    serial_number TEXT NOT NULL,
                    port_number INTEGER NOT NULL,
                    today_production INTEGER NOT NULL,
                    total_production INTEGER NOT NULL,
                    last_updated TIMESTAMP NOT NULL,
                    PRIMARY KEY (serial_number, port_number)
                )
            ''')
            
            # Configuration cache table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config_cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    last_updated TIMESTAMP NOT NULL
                )
            ''')
            
            # Metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    timestamp TIMESTAMP NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    tags TEXT
                )
            ''')
            
            # Create indices
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
                ON metrics(timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_metrics_name 
                ON metrics(metric_name)
            ''')
            
            self.connection.commit()
            logger.info(f"Database initialized at {self.database_path}")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            self.enabled = False
    
    def save_production_cache(self, serial_number: str, port_number: int, 
                            today_production: int, total_production: int) -> None:
        """Save production cache for an inverter port.
        
        Args:
            serial_number: Inverter serial number
            port_number: Port number
            today_production: Today's production value
            total_production: Total production value
        """
        if not self.enabled or not self.connection:
            return
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO production_cache 
                (serial_number, port_number, today_production, total_production, last_updated)
                VALUES (?, ?, ?, ?, ?)
            ''', (serial_number, port_number, today_production, total_production, datetime.now()))
            
            self.connection.commit()
            logger.debug(f"Saved production cache for {serial_number} port {port_number}")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to save production cache: {e}")
    
    def load_production_cache(self) -> Dict[Tuple[str, int], Tuple[int, int]]:
        """Load production cache for all inverter ports.
        
        Returns:
            Dictionary mapping (serial_number, port_number) to (today_production, total_production)
        """
        if not self.enabled or not self.connection:
            return {}
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM production_cache')
            
            cache = {}
            for row in cursor.fetchall():
                key = (row['serial_number'], row['port_number'])
                value = (row['today_production'], row['total_production'])
                cache[key] = value
            
            logger.info(f"Loaded production cache for {len(cache)} inverter ports")
            return cache
            
        except sqlite3.Error as e:
            logger.error(f"Failed to load production cache: {e}")
            return {}
    
    def clear_today_production(self) -> None:
        """Clear today's production values (called at daily reset)."""
        if not self.enabled or not self.connection:
            return
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('UPDATE production_cache SET today_production = 0')
            self.connection.commit()
            logger.info("Cleared today's production cache")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to clear today's production: {e}")
    
    def save_config(self, key: str, value: Any) -> None:
        """Save configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value (will be JSON serialized)
        """
        if not self.enabled or not self.connection:
            return
        
        try:
            cursor = self.connection.cursor()
            value_json = json.dumps(value)
            cursor.execute('''
                INSERT OR REPLACE INTO config_cache (key, value, last_updated)
                VALUES (?, ?, ?)
            ''', (key, value_json, datetime.now()))
            
            self.connection.commit()
            
        except sqlite3.Error as e:
            logger.error(f"Failed to save config: {e}")
    
    def load_config(self, key: str, default: Any = None) -> Any:
        """Load configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        if not self.enabled or not self.connection:
            return default
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT value FROM config_cache WHERE key = ?', (key,))
            row = cursor.fetchone()
            
            if row:
                return json.loads(row['value'])
            return default
            
        except sqlite3.Error as e:
            logger.error(f"Failed to load config: {e}")
            return default
    
    def save_metric(self, metric_name: str, metric_value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Save a metric value.
        
        Args:
            metric_name: Metric name
            metric_value: Metric value
            tags: Optional tags for the metric
        """
        if not self.enabled or not self.connection:
            return
        
        try:
            cursor = self.connection.cursor()
            tags_json = json.dumps(tags) if tags else None
            cursor.execute('''
                INSERT INTO metrics (timestamp, metric_name, metric_value, tags)
                VALUES (?, ?, ?, ?)
            ''', (datetime.now(), metric_name, metric_value, tags_json))
            
            self.connection.commit()
            
        except sqlite3.Error as e:
            logger.error(f"Failed to save metric: {e}")
    
    def get_metrics(self, metric_name: str, since: Optional[datetime] = None, limit: int = 1000) -> list:
        """Get historical metrics.
        
        Args:
            metric_name: Metric name to query
            since: Optional start time
            limit: Maximum number of records to return
            
        Returns:
            List of metric records
        """
        if not self.enabled or not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            
            if since:
                cursor.execute('''
                    SELECT * FROM metrics 
                    WHERE metric_name = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (metric_name, since, limit))
            else:
                cursor.execute('''
                    SELECT * FROM metrics 
                    WHERE metric_name = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (metric_name, limit))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            logger.error(f"Failed to get metrics: {e}")
            return []
    
    def cleanup_old_metrics(self, days: int = 30) -> None:
        """Delete metrics older than specified days.
        
        Args:
            days: Number of days to keep
        """
        if not self.enabled or not self.connection:
            return
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                DELETE FROM metrics 
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            ''', (days,))
            
            deleted = cursor.rowcount
            self.connection.commit()
            
            if deleted > 0:
                logger.info(f"Deleted {deleted} old metric records")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to cleanup old metrics: {e}")
    
    def backup_database(self, backup_path: Optional[Path] = None) -> bool:
        """Create a backup of the database.
        
        Args:
            backup_path: Optional custom backup path
            
        Returns:
            True if backup successful
        """
        if not self.enabled or not self.connection:
            return False
        
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = self.database_path.parent / f"{self.database_path.stem}_backup_{timestamp}.db"
            
            # Ensure backup directory exists
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use SQLite backup API for safe backup
            backup_conn = sqlite3.connect(str(backup_path))
            self.connection.backup(backup_conn)
            backup_conn.close()
            
            logger.info(f"Database backed up to {backup_path}")
            return True
            
        except (sqlite3.Error, OSError) as e:
            logger.error(f"Failed to backup database: {e}")
            return False
    
    def vacuum(self) -> None:
        """Vacuum the database to reclaim space."""
        if not self.enabled or not self.connection:
            return
        
        try:
            self.connection.execute('VACUUM')
            logger.info("Database vacuumed")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to vacuum database: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        if not self.enabled or not self.connection:
            return {}
        
        try:
            cursor = self.connection.cursor()
            
            # Get table counts
            cursor.execute('SELECT COUNT(*) FROM production_cache')
            production_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM config_cache')
            config_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM metrics')
            metrics_count = cursor.fetchone()[0]
            
            # Get database size
            db_size = self.database_path.stat().st_size if self.database_path.exists() else 0
            
            return {
                'database_path': str(self.database_path),
                'database_size_bytes': db_size,
                'production_cache_entries': production_count,
                'config_cache_entries': config_count,
                'metrics_entries': metrics_count,
            }
            
        except (sqlite3.Error, OSError) as e:
            logger.error(f"Failed to get database statistics: {e}")
            return {}
    
    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            try:
                self.connection.commit()
                self.connection.close()
                logger.info("Database connection closed")
            except sqlite3.Error as e:
                logger.error(f"Error closing database: {e}")
            finally:
                self.connection = None

