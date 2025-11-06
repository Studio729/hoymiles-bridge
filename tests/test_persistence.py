"""Tests for persistence module."""

import tempfile
from pathlib import Path

import pytest

from hoymiles_smiles.persistence import PersistenceManager


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    
    yield db_path
    
    # Cleanup
    if db_path.exists():
        db_path.unlink()


def test_persistence_initialization(temp_db):
    """Test persistence manager initialization."""
    pm = PersistenceManager(temp_db, enabled=True)
    assert pm.enabled is True
    assert pm.database_path == temp_db
    assert temp_db.exists()
    pm.close()


def test_save_and_load_production_cache(temp_db):
    """Test saving and loading production cache."""
    pm = PersistenceManager(temp_db, enabled=True)
    
    # Save data
    pm.save_production_cache("SN12345", 1, 1000, 50000)
    pm.save_production_cache("SN12345", 2, 1100, 51000)
    
    # Load data
    cache = pm.load_production_cache()
    assert len(cache) == 2
    assert cache[("SN12345", 1)] == (1000, 50000)
    assert cache[("SN12345", 2)] == (1100, 51000)
    
    pm.close()


def test_clear_today_production(temp_db):
    """Test clearing today's production."""
    pm = PersistenceManager(temp_db, enabled=True)
    
    # Save data
    pm.save_production_cache("SN12345", 1, 1000, 50000)
    
    # Clear today's production
    pm.clear_today_production()
    
    # Verify
    cache = pm.load_production_cache()
    assert cache[("SN12345", 1)][0] == 0  # today_production should be 0
    assert cache[("SN12345", 1)][1] == 50000  # total_production unchanged
    
    pm.close()


def test_save_and_load_config(temp_db):
    """Test saving and loading configuration."""
    pm = PersistenceManager(temp_db, enabled=True)
    
    # Save config
    pm.save_config("test_key", {"value": 123, "name": "test"})
    
    # Load config
    loaded = pm.load_config("test_key")
    assert loaded == {"value": 123, "name": "test"}
    
    # Load non-existent key
    default = pm.load_config("non_existent", default="default_value")
    assert default == "default_value"
    
    pm.close()


def test_save_metrics(temp_db):
    """Test saving metrics."""
    pm = PersistenceManager(temp_db, enabled=True)
    
    # Save metrics
    pm.save_metric("power", 1500.0, {"dtu": "DTU1"})
    pm.save_metric("power", 1600.0, {"dtu": "DTU1"})
    
    # Get metrics
    metrics = pm.get_metrics("power")
    assert len(metrics) == 2
    
    pm.close()


def test_backup_database(temp_db):
    """Test database backup."""
    pm = PersistenceManager(temp_db, enabled=True)
    
    # Save some data
    pm.save_production_cache("SN12345", 1, 1000, 50000)
    
    # Backup
    backup_path = temp_db.parent / "backup.db"
    success = pm.backup_database(backup_path)
    assert success is True
    assert backup_path.exists()
    
    # Cleanup
    if backup_path.exists():
        backup_path.unlink()
    
    pm.close()


def test_disabled_persistence(temp_db):
    """Test persistence when disabled."""
    pm = PersistenceManager(temp_db, enabled=False)
    
    # Operations should not fail but not do anything
    pm.save_production_cache("SN12345", 1, 1000, 50000)
    cache = pm.load_production_cache()
    assert len(cache) == 0
    
    pm.close()

