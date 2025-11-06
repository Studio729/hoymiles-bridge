# Update v1.1.2 - Initial State History Fix

## Issue Fixed

**Problem**: When the custom component is first installed, the activity/history doesn't show the initial state. The sensor shows "Connected" but the history shows "unavailable" as the last state, which is confusing.

**Root Cause**: Home Assistant doesn't automatically record the initial state of entities when they're first added. The entity needs to explicitly write its initial state to the recorder/history.

**Solution**: Added `async_added_to_hass()` method to both sensor and binary_sensor entities that forces an initial state write when the entity is first added.

---

## What Changed

### Files Modified
- `custom_components/hoymiles_smiles/binary_sensor.py` - Added initial state write
- `custom_components/hoymiles_smiles/sensor.py` - Added initial state write
- `custom_components/hoymiles_smiles/manifest.json` - Version bumped to 1.1.2

### Code Added
```python
async def async_added_to_hass(self) -> None:
    """Handle entity added to hass."""
    await super().async_added_to_hass()
    
    # Force initial state write to recorder/history
    _LOGGER.debug(
        "[Initial State] Writing initial state for %s: %s (available=%s)",
        self.name,
        self.state,
        self.available
    )
    
    # Trigger a state update to ensure history reflects initial state
    self.async_write_ha_state()
```

---

## Expected Behavior

### Before (v1.1.1)
```
Install integration → Sensor shows "on" → History shows "unavailable"
                                        ↑
                                   Confusing!
```

### After (v1.1.2)
```
Install integration → Sensor shows "on" → History shows "on"
                                        ↑
                                    Correct!
```

---

## Installation

### Step 1: Copy Updated Files
```bash
cd /Users/tim/Downloads/hoymiles-smiles-main
cp -r custom_components/hoymiles_smiles /config/custom_components/
```

### Step 2: Restart Home Assistant
```
Settings → System → Restart
```

### Step 3: Test (Optional)
To verify the fix works:

1. **Delete the integration** (Settings → Devices & Services → Hoymiles MQTT Bridge → Delete)
2. **Restart Home Assistant**
3. **Re-add the integration** (Settings → Devices & Services → Add Integration)
4. **Check history immediately**:
   - Go to the "Application Healthy" sensor
   - Click "Show more" on the history graph
   - You should see the current state (not "unavailable")

---

## Debug Logging

With debug logging enabled, you'll now see:
```
[Initial State] Writing initial state for Application Healthy sensor: on (available=True)
[Initial State] Writing initial state for Uptime sensor: 3600 (available=True)
[Initial State] Writing initial state for MQTT Messages Published sensor: 1200 (available=True)
... (for all 9 entities)
```

This confirms the initial state was written to the recorder.

---

## Version History

- **v1.1.2** (2024-11-05): Fixed initial state history
- **v1.1.1** (2024-11-05): Enhanced debug logging + icon fix
- **v1.1.0** (2024-11-05): Fixed intermittent unavailability
- **v1.0.0** (2024-11-04): Initial custom integration release

---

## Note

This is a minor cosmetic fix that improves the user experience when first installing the integration. It doesn't affect functionality - the sensor always worked correctly, it was just the history display that was confusing.

**Status**: Ready to install ✅

