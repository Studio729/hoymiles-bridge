# Hoymiles MQTT Custom Integration - Developer Guide

## 📚 What Is This?

This is a **native Home Assistant custom integration** for monitoring your Hoymiles MQTT Bridge application. It follows the [Home Assistant Core developer guidelines](https://developers.home-assistant.io/docs/development_index/) and provides a professional, UI-based integration experience.

---

## 🎯 Integration vs YAML Configuration

### Two Approaches Available

#### 1. **YAML Configuration** (`home_assistant_sensors.yaml`)
- Uses REST and template platforms
- Configured through YAML files
- Requires manual editing
- Good for simple setups

#### 2. **Custom Integration** (this one!)
- Native Python-based integration
- Configured through UI
- Appears in Integrations page
- Professional experience
- Better performance
- Device registry integration

---

## 🏗️ Architecture

### File Structure

```
custom_components/hoymiles_smiles/
├── __init__.py              # Integration setup and entry point
├── manifest.json            # Integration metadata
├── const.py                 # Constants and sensor definitions
├── coordinator.py           # Data fetching and coordination
├── config_flow.py           # UI configuration flow
├── sensor.py                # Sensor entities
├── binary_sensor.py         # Binary sensor entities
├── strings.json             # UI strings (English)
└── .translations/
    └── en.json              # Translated strings
```

### Component Overview

#### 1. **`manifest.json`** - Integration Metadata

Defines the integration's identity and requirements based on [manifest documentation](https://developers.home-assistant.io/docs/creating_integration_manifest/):

```json
{
  "domain": "hoymiles_smiles",
  "name": "Hoymiles MQTT Bridge",
  "config_flow": true,
  "iot_class": "local_polling",
  "requirements": ["aiohttp>=3.9.0"],
  "version": "1.0.0",
  "integration_type": "device"
}
```

**Key Fields:**
- `domain`: Unique identifier for the integration
- `config_flow`: Enables UI-based configuration
- `iot_class`: "local_polling" means it polls a local API
- `integration_type`: "device" groups all entities under one device

---

#### 2. **`__init__.py`** - Integration Setup

Handles integration lifecycle based on [integration setup documentation](https://developers.home-assistant.io/docs/creating_component_index/):

```python
async def async_setup_entry(hass, entry):
    """Set up from config entry."""
    # 1. Create coordinator
    coordinator = HoymilesMqttCoordinator(...)
    
    # 2. Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # 3. Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # 4. Forward to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True
```

**Key Functions:**
- `async_setup_entry`: Called when integration is added
- `async_unload_entry`: Called when integration is removed
- `async_reload_entry`: Called when options change

---

#### 3. **`coordinator.py`** - Data Update Coordinator

Uses Home Assistant's [DataUpdateCoordinator](https://developers.home-assistant.io/docs/integration_fetching_data/) for efficient data fetching:

```python
class HoymilesMqttCoordinator(DataUpdateCoordinator):
    """Manage data fetching."""
    
    async def _async_update_data(self):
        """Fetch data from API."""
        # Fetch /health endpoint
        health_data = await self._fetch_endpoint(session, ENDPOINT_HEALTH)
        
        # Fetch /stats endpoint
        stats_data = await self._fetch_endpoint(session, ENDPOINT_STATS)
        
        return {"health": health_data, "stats": stats_data}
```

**Benefits:**
- Automatic retry logic
- Debouncing (prevents excessive API calls)
- All entities update together
- Error handling built-in
- Efficient polling

---

#### 4. **`config_flow.py`** - UI Configuration

Implements [config flow](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/) for UI-based setup:

```python
class HoymilesMqttConfigFlow(config_entries.ConfigFlow):
    """Handle config flow."""
    
    async def async_step_user(self, user_input):
        """Handle initial step."""
        # 1. Validate connection
        await validate_connection(host, port)
        
        # 2. Check if already configured
        await self.async_set_unique_id(f"{host}:{port}")
        
        # 3. Create entry
        return self.async_create_entry(title=..., data=user_input)
```

**Features:**
- User-friendly setup wizard
- Connection validation
- Prevents duplicate entries
- Options flow for runtime config

---

#### 5. **`sensor.py`** - Sensor Entities

Implements sensor entities following [entity documentation](https://developers.home-assistant.io/docs/core/entity/sensor/):

```python
class HoymilesMqttSensor(CoordinatorEntity, SensorEntity):
    """Sensor entity."""
    
    @property
    def native_value(self):
        """Return sensor value."""
        return self.entity_description.value_fn(self.coordinator)
    
    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        return self.entity_description.attributes_fn(self.coordinator)
```

**Features:**
- 8 sensor entities
- Proper device classes (duration, etc.)
- State classes (measurement, total_increasing)
- Extra attributes for additional data
- Diagnostic entities (database stats)

---

#### 6. **`binary_sensor.py`** - Binary Sensor

Implements health status as a [binary sensor](https://developers.home-assistant.io/docs/core/entity/binary-sensor/):

```python
class HoymilesMqttHealthBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Health binary sensor."""
    
    @property
    def is_on(self):
        """Return if healthy."""
        health = self.coordinator.get_health_data()
        return health.get("healthy", False)
    
    @property
    def icon(self):
        """Dynamic icon based on state."""
        return "mdi:check-circle" if self.is_on else "mdi:alert-circle"
```

**Features:**
- Connectivity device class
- Dynamic icon
- Rich attributes (DTU status, MQTT stats)
- On = healthy, Off = unhealthy

---

## 🔄 Data Flow

### 1. Integration Setup
```
User adds integration
    ↓
Config flow validates connection
    ↓
Integration creates coordinator
    ↓
Coordinator fetches initial data
    ↓
Platforms create entities
    ↓
Entities registered in HA
```

### 2. Data Updates
```
Timer triggers (scan_interval)
    ↓
Coordinator fetches /health and /stats
    ↓
Data stored in coordinator.data
    ↓
All entities notified of update
    ↓
Entities read from coordinator
    ↓
States updated in HA
```

### 3. User Interaction
```
User clicks "Configure"
    ↓
Options flow shows form
    ↓
User changes scan_interval
    ↓
Integration reloads
    ↓
New coordinator created with new interval
```

---

## 🎨 Entity Naming Convention

Entities follow Home Assistant naming standards:

### Format
```
{platform}.{domain}_{device}_{description}
```

### Examples
```
sensor.hoymiles_smiles_bridge_uptime
sensor.hoymiles_smiles_bridge_mqtt_messages_published
binary_sensor.hoymiles_smiles_bridge_application_healthy
```

### Unique IDs
```python
self._attr_unique_id = f"{entry.entry_id}_{description.key}"
```

This ensures entities remain stable across renames and config changes.

---

## 🔌 Device Integration

All entities are grouped under one device:

```python
{
    "identifiers": {(DOMAIN, entry.entry_id)},
    "name": "Hoymiles MQTT Bridge",
    "manufacturer": "Hoymiles",
    "model": "MQTT Bridge",
    "sw_version": "0.12.0",
}
```

**Benefits:**
- All entities visible on device page
- Easy management
- Device automation support
- Better organization

---

## 🔧 Customization Guide

### Adding New Sensors

To add a new sensor, edit `sensor.py`:

```python
HoymilesMqttSensorEntityDescription(
    key="my_new_sensor",
    name="My New Sensor",
    icon="mdi:new-box",
    native_unit_of_measurement="units",
    state_class=SensorStateClass.MEASUREMENT,
    value_fn=lambda coordinator: (
        coordinator.get_health_data().get("my_value")
        if coordinator.get_health_data()
        else None
    ),
),
```

### Changing Update Interval

Users can change via UI:
1. Settings → Devices & Services
2. Hoymiles MQTT Bridge → Configure
3. Adjust "Scan interval"

Or programmatically in `const.py`:
```python
DEFAULT_SCAN_INTERVAL: Final = 30  # Change from 60 to 30
```

### Adding Attributes

In sensor description:
```python
attributes_fn=lambda coordinator: {
    "my_attribute": coordinator.get_health_data().get("value"),
    "another_attribute": "static_value",
}
```

### Supporting Multiple DTUs

Currently hardcoded to "DTU". To support multiple:

1. Detect DTU names from API response
2. Create sensor entity for each DTU
3. Use DTU name in unique_id and name

---

## 📊 Comparison: YAML vs Custom Integration

| Feature | YAML Config | Custom Integration |
|---------|-------------|-------------------|
| **Setup Method** | Manual YAML editing | UI wizard |
| **Configuration Location** | `configuration.yaml` or packages | Settings → Integrations |
| **Updates** | Edit YAML, restart | UI or reload integration |
| **Device Grouping** | No | Yes (all entities under device) |
| **Entity Registry** | Partial | Full |
| **Unique IDs** | Manual | Automatic |
| **Options Flow** | No (edit YAML) | Yes (UI) |
| **Error Handling** | Template-based | Python exception handling |
| **Performance** | REST calls every interval | DataUpdateCoordinator (optimized) |
| **Discoverability** | Hidden in YAML | Visible in UI |
| **User Experience** | Technical | User-friendly |
| **Development** | YAML knowledge | Python knowledge |
| **Debugging** | Template editor | Python logs |

---

## 🧪 Testing

### Manual Testing

1. **Install integration**
2. **Verify entities created**:
   - Developer Tools → States
   - Search for "hoymiles_smiles_bridge"
3. **Check values updating**:
   - Watch entity states
   - Refresh should fetch new data
4. **Test options**:
   - Click Configure
   - Change scan interval
   - Verify updates faster/slower
5. **Test removal**:
   - Delete integration
   - Verify entities removed

### Automated Testing

Create `test_config_flow.py`:
```python
async def test_form(hass):
    """Test config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
```

---

## 🐛 Debugging

### Enable Debug Logging

In `configuration.yaml`:
```yaml
logger:
  default: warning
  logs:
    custom_components.hoymiles_smiles: debug
```

### Common Issues

#### "Integration not found"
- Check files are in `/config/custom_components/hoymiles_smiles/`
- Verify `manifest.json` is valid JSON
- Restart HA

#### "Cannot connect" during setup
- Check API is accessible: `curl http://host:port/health`
- Verify network connectivity
- Check firewall rules

#### Sensors show "unavailable"
- Check coordinator logs for errors
- Verify API endpoints return data
- Check scan interval isn't too frequent

#### Entities not updating
- Check coordinator update interval
- Look for errors in logs
- Verify API is responding correctly

---

## 📚 Home Assistant Core References

This integration follows these official guidelines:

1. **[Development Index](https://developers.home-assistant.io/docs/development_index/)** - Overview
2. **[Creating Integration](https://developers.home-assistant.io/docs/creating_component_index/)** - Setup
3. **[Config Flow](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/)** - UI configuration
4. **[Data Coordinator](https://developers.home-assistant.io/docs/integration_fetching_data/)** - Data fetching
5. **[Sensor Entity](https://developers.home-assistant.io/docs/core/entity/sensor/)** - Sensor implementation
6. **[Binary Sensor](https://developers.home-assistant.io/docs/core/entity/binary-sensor/)** - Binary sensor
7. **[Manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/)** - Metadata

---

## 🚀 Future Enhancements

Possible improvements:

### 1. Services
Add custom services:
```python
async def async_refresh_data(call):
    """Service to manually refresh data."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_request_refresh()
```

### 2. Diagnostics
Add diagnostics download:
```python
async def async_get_config_entry_diagnostics(hass, entry):
    """Return diagnostics."""
    return {
        "coordinator_data": coordinator.data,
        "last_update": coordinator.last_update_success_time,
    }
```

### 3. Multiple DTUs
Support multiple DTUs:
- Detect DTU names from API
- Create entity for each DTU
- Allow enabling/disabling specific DTUs

### 4. WebSocket Support
Instead of polling, use WebSocket for real-time updates.

### 5. Configuration via UI
Add more options:
- Enable/disable specific sensors
- Custom entity names
- Alert thresholds

---

## 📖 Code Examples

### Adding a Service

In `__init__.py`:
```python
async def async_setup_entry(hass, entry):
    # ... existing code ...
    
    async def handle_refresh(call):
        """Handle refresh service."""
        await coordinator.async_request_refresh()
    
    hass.services.async_register(
        DOMAIN,
        "refresh",
        handle_refresh,
    )
```

### Adding Diagnostics

Create `diagnostics.py`:
```python
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict:
    """Return diagnostics for config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    return {
        "health_data": coordinator.get_health_data(),
        "stats_data": coordinator.get_stats_data(),
        "last_update_success": coordinator.last_update_success,
        "update_interval": coordinator.update_interval.total_seconds(),
    }
```

---

## ✅ Summary

This custom integration provides:

✅ **Native HA experience** - UI-based, professional
✅ **Efficient data fetching** - DataUpdateCoordinator
✅ **Device integration** - All entities grouped
✅ **Configurable** - Options flow for runtime config
✅ **Robust** - Proper error handling
✅ **Maintainable** - Clean code structure
✅ **Extensible** - Easy to add features
✅ **Well-documented** - Following HA standards

**Perfect for users who want a professional integration experience!** 🌟

---

## 🆘 Support

- **Installation Guide**: `CUSTOM_INTEGRATION_INSTALL.md`
- **Home Assistant Docs**: [developers.home-assistant.io](https://developers.home-assistant.io)
- **Integration Type**: Native Python integration
- **Compatibility**: Home Assistant 2024.2+

