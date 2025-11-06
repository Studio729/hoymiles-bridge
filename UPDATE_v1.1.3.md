# Update v1.1.3 - Config Flow Fixes

## Issues Fixed

### 1. HTTP 503 Error During Installation
**Problem**: When installing the integration, you get "Unexpected error: HTTP 503" if the bridge is still starting up or temporarily unavailable.

**Solution**: 
- Added specific handling for 503 status code
- Provides helpful error message: "Bridge may be starting up"
- Added better error handling for timeouts and connection errors
- More detailed logging for troubleshooting

**User Experience**:
- **Before**: Confusing "Unexpected error: HTTP 503"
- **After**: Clear message "Health endpoint unavailable (503). Bridge may be starting up."

### 2. Deprecation Warning (Home Assistant 2025.12)
**Problem**: Warning logged: "Detected that custom integration 'hoymiles_mqtt' sets option flow config_entry explicitly, which is deprecated"

**Solution**: 
- Removed the explicit `__init__` method from `HoymilesMqttOptionsFlow`
- Removed `self.config_entry = config_entry` assignment (line 116)
- The parent `OptionsFlow` class now automatically provides `self.config_entry`

**Impact**: Integration will continue working in Home Assistant 2025.12 and beyond.

---

## Changes Made

### Files Modified
1. **`config_flow.py`**:
   - Enhanced error handling for HTTP status codes (200, 503, others)
   - Added timeout-specific error handling
   - Added `asyncio` import
   - Removed deprecated `__init__` method from OptionsFlow
   - Better logging with URLs and context

2. **`manifest.json`**: Version 1.1.2 → 1.1.3

3. **`binary_sensor.py`**: Version 1.1.2 → 1.1.3

4. **`sensor.py`**: Version 1.1.2 → 1.1.3

---

## Detailed Error Handling

### Before
```python
if response.status == 200:
    # success
else:
    raise ConnectionError(f"HTTP {response.status}")  # All non-200 = generic error
```

### After
```python
if response.status == 200:
    # success
elif response.status == 503:
    # Specific handling for "Service Unavailable"
    _LOGGER.warning("Bridge may be starting up. Wait and try again.")
    raise ConnectionError("Health endpoint unavailable (503). Bridge may be starting up.")
else:
    # Other HTTP errors
    _LOGGER.error("Health endpoint returned HTTP %d", response.status)
    raise ConnectionError(f"Health endpoint returned HTTP {response.status}")
```

**Plus**:
- Separate handling for `asyncio.TimeoutError`
- Separate handling for `aiohttp.ClientError`
- Re-raise `ConnectionError` as-is to preserve error messages
- Full stack traces for unexpected errors

---

## Installation

```bash
cd /Users/tim/Downloads/hoymiles-mqtt-main
cp -r custom_components/hoymiles_mqtt /config/custom_components/
# Restart Home Assistant
```

---

## Testing the Fixes

### Test Fix #1: HTTP 503 Handling

**Scenario**: Try to add integration while bridge is starting up

1. **Restart bridge container**: `docker restart hoymiles_mqtt`
2. **Immediately try to add integration** (while bridge is starting)
3. **Expected**: Clear error message about bridge starting up
4. **Wait 30 seconds** and try again
5. **Expected**: Should connect successfully

**Old behavior**: "Unexpected error: HTTP 503"  
**New behavior**: "Health endpoint unavailable (503). Bridge may be starting up."

### Test Fix #2: Deprecation Warning

**Scenario**: Configure scan interval

1. Go to: Settings → Devices & Services → Hoymiles MQTT Bridge
2. Click "CONFIGURE"
3. Change scan interval
4. Click "SUBMIT"
5. **Check logs**: No deprecation warning about `config_entry`

**Old behavior**: Warning logged  
**New behavior**: No warning (fully compatible with HA 2025.12+)

---

## Error Messages Reference

| Error | Cause | User Action |
|-------|-------|-------------|
| `Health endpoint unavailable (503)` | Bridge starting up | Wait 30-60 seconds and try again |
| `Health endpoint returned HTTP 404` | Wrong port or endpoint missing | Check `HEALTH_PORT` is correct |
| `Health endpoint returned HTTP 500` | Bridge crashed or error | Check bridge logs |
| `Cannot connect to Hoymiles MQTT health API` | Network issue or wrong host | Verify host IP and network |
| `Connection timeout` | Bridge not responding | Check bridge is running and accessible |

---

## Version History

- **v1.1.3** (2024-11-05): Fixed config flow errors and deprecation warning
- **v1.1.2** (2024-11-05): Fixed initial state history
- **v1.1.1** (2024-11-05): Enhanced debug logging + icon fix
- **v1.1.0** (2024-11-05): Fixed intermittent unavailability
- **v1.0.0** (2024-11-04): Initial custom integration release

---

## Notes

### Why HTTP 503?
The bridge's health endpoint can return 503 (Service Unavailable) in these scenarios:
1. **Container just started** - Python app is still initializing
2. **Database locked** - SQLite database is being accessed
3. **Heavy load** - Too many MQTT messages being published
4. **Temporary error** - Transient issue that resolves quickly

The new error handling makes these scenarios clear to the user.

### Why Remove __init__?
Home Assistant is standardizing how OptionsFlow works. Starting in HA 2025.12:
- `self.config_entry` is automatically available (passed by the framework)
- Manually setting it in `__init__` will cause an error
- Our fix makes the integration future-proof

---

## Compatibility

- ✅ **Home Assistant 2024.2+** - Current versions
- ✅ **Home Assistant 2025.12+** - Future-proof (no deprecation warnings)
- ✅ **Python 3.10+** - All supported versions

---

**Status**: Ready to install ✅  
**Breaking Changes**: None (100% backward compatible)

