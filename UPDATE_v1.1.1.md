# Update v1.1.1 - Debug Logging & Icon Fix

## Changes

### 1. Enhanced Debug Logging
Added comprehensive debug logging to track API calls and diagnose intermittent unavailability:

- **`[API Call Start]`** - Logs when update cycle begins with session state
- **`[API Call]`** - Logs each endpoint fetch (health, stats)
- **`[HTTP]`** - Logs individual HTTP requests with timing
- **`[API Call Complete]`** - Logs successful completion with total time
- **`[API Call Failed]`** - Logs failures with detailed error information
- **`[Session]`** - Logs session lifecycle events

### 2. Fixed Icon Display
- Resized icon from 60x60 to 256x256 (proper HA standard)
- Added high-resolution icon@2x.png (512x512) for retina displays
- Bumped version to 1.1.1

---

## Installation

### Quick Update
```bash
cd /Users/tim/Downloads/hoymiles-mqtt-main
cp -r custom_components/hoymiles_mqtt /config/custom_components/
```

### Clear Home Assistant Cache
```bash
# In Home Assistant container or host
rm -rf /config/.storage/core.restore_state
rm -rf /config/custom_components/.cache
```

### Restart Home Assistant
```
Settings → System → Restart
```

### Force Icon Refresh
1. Clear browser cache: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
2. Try incognito/private window
3. Hard refresh the Integrations page
4. If still not showing, delete and re-add the integration

---

## Enable Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.hoymiles_mqtt: debug
    custom_components.hoymiles_mqtt.coordinator: debug
```

**Restart Home Assistant**

---

## What to Look For in Logs

### Normal Operation
```
[API Call Start] Fetching data from 192.168.1.191:8090 (session_active=True, consecutive_failures=0)
[API Call] Fetching /health from 192.168.1.191:8090
[HTTP] GET http://192.168.1.191:8090/health
[HTTP] Response 200 from /health in 0.123s
[HTTP] Successfully parsed JSON from /health (450 bytes)
[API Call] Received health data: healthy=True, uptime=3600
[API Call] Fetching /stats from 192.168.1.191:8090
[HTTP] GET http://192.168.1.191:8090/stats
[HTTP] Response 200 from /stats in 0.098s
[HTTP] Successfully parsed JSON from /stats (250 bytes)
[API Call] Received stats data: records=120
[API Call Complete] Success in 0.25s from 192.168.1.191:8090
```

### Intermittent Failures (what we're looking for)
```
[API Call Start] Fetching data from 192.168.1.191:8090 (session_active=True, consecutive_failures=0)
[API Call] Fetching /health from 192.168.1.191:8090
[HTTP] GET http://192.168.1.191:8090/health
[HTTP] Timeout for /health
Retry 1/2 for /health after TimeoutError, waiting 0.5s
[HTTP] GET http://192.168.1.191:8090/health
[HTTP] Response 200 from /health in 0.156s
[API Call] Received health data: healthy=True, uptime=3601
... success after retry ...
```

### Persistent Failures
```
[API Call Start] Fetching data from 192.168.1.191:8090 (session_active=True, consecutive_failures=0)
[API Call] Fetching /health from 192.168.1.191:8090
[HTTP] GET http://192.168.1.191:8090/health
[HTTP] Timeout for /health
Retry 1/2 for /health after TimeoutError, waiting 0.5s
[HTTP] GET http://192.168.1.191:8090/health
[HTTP] Timeout for /health
All 2 retries failed for /health: TimeoutError()
[API Call Failed] Timeout after 2.51s from 192.168.1.191:8090 (failure 1): 
[API Call Failed] Session state: active=True, closed=False
[Session] Closing session due to timeout
```

---

## Diagnostic Questions

When you see unavailability, check the logs for:

1. **What triggers it?**
   - Does it happen at specific times?
   - After how many successful calls?
   - Any pattern to the interval (30-40 min you mentioned)?

2. **What's the failure mode?**
   - Timeout? (`[HTTP] Timeout for /health`)
   - Connection refused? (`[HTTP] Response error 403/404/500`)
   - Network error? (`ClientConnectorError`)

3. **Session state when it fails?**
   - `session_active=True` or `False`?
   - Does it close and recreate the session?

4. **How long does each call take?**
   - Look at timing in `[API Call Complete]` and `[HTTP] Response`
   - Are timeouts gradual (getting slower) or sudden?

5. **Does retry help?**
   - Do you see retries succeeding?
   - Or do all 2 retries fail?

---

## Additional Diagnostics

### Test Health Endpoint Directly
While monitoring HA logs, test the endpoint:

```bash
# Run this every 10 seconds and watch for failures
while true; do 
  time curl -s -w "\nHTTP %{http_code} in %{time_total}s\n" \
    http://192.168.1.191:8090/health | head -1
  sleep 10
done
```

Compare failures in this test with "unavailable" events in HA.

### Check Bridge Container Logs
```bash
docker logs -f hoymiles_mqtt --tail 100
```

Look for:
- Health endpoint being called
- Any blocking operations during that time
- MQTT publishing activity (could block if heavy)

### Network Monitoring
```bash
# Check for packet loss
ping -c 100 192.168.1.191

# Check for network congestion
mtr 192.168.1.191
```

---

## Possible Root Causes

Based on debug logs, we can determine:

### 1. Bridge Application Blocking
**Symptoms**: Timeouts occur exactly every 30-40 minutes  
**Debug shows**: Connection attempts time out, not refused  
**Solution**: Check bridge logs for blocking operations

### 2. Network Issues
**Symptoms**: Intermittent timeouts, no pattern  
**Debug shows**: Random `ClientConnectorError` or timeouts  
**Solution**: Check network stability, WiFi signal, switch health

### 3. Home Assistant Event Loop Blocking
**Symptoms**: Multiple integrations show unavailable simultaneously  
**Debug shows**: No logs during unavailability (HA frozen)  
**Solution**: Check HA system resources, database size

### 4. Rate Limiting / Resource Exhaustion
**Symptoms**: Happens after N successful calls  
**Debug shows**: Success count matches pattern  
**Solution**: Increase scan_interval, check bridge resources

### 5. Session/Connection Pool Issues
**Symptoms**: Happens when session is reused too long  
**Debug shows**: `session_active=True` but requests fail  
**Solution**: We can force session recreation more frequently

---

## Quick Fixes to Try

### Fix 1: Increase Scan Interval
```
Settings → Devices & Services → Hoymiles MQTT Bridge → Configure
Scan Interval: 60 → 90 seconds
```

### Fix 2: Test with Fresh Session Each Time
If debug logs show session is active but failing, I can modify the code to recreate the session more aggressively.

### Fix 3: Increase Timeout
If logs show calls taking 15-19 seconds (near the 20s limit), I can increase the timeout.

### Fix 4: Add Connection Keepalive
If logs show connection dropping, I can add TCP keepalive settings.

---

## Reporting Back

When you have debug logs, please provide:

1. **The full debug log sequence** from `[API Call Start]` through the failure
2. **Timestamp of unavailability** in HA
3. **Bridge logs** during that same timestamp
4. **Pattern observed**: Every X minutes? After Y successful calls?
5. **Network test results** if you ran them

This will help pinpoint the exact cause!

---

## Icon Troubleshooting

If icon still doesn't show after update:

1. **Verify files exist**:
   ```bash
   ls -lh /config/custom_components/hoymiles_mqtt/icon*.png
   ```
   Should show:
   - `icon.png` (20K, 256x256)
   - `icon@2x.png` (56K, 512x512)

2. **Check file permissions**:
   ```bash
   chmod 644 /config/custom_components/hoymiles_mqtt/icon*.png
   ```

3. **Delete integration cache**:
   ```bash
   rm -rf /config/.storage/core.entity_registry
   ```
   ⚠️ **Warning**: This will require you to re-add the integration

4. **Last resort**: Delete and re-add the integration
   - Settings → Devices & Services
   - Click "..." on Hoymiles MQTT Bridge
   - Click "Delete"
   - Restart HA
   - Re-add integration

---

**Version**: 1.1.1  
**Date**: November 5, 2024  
**Changes**: Enhanced debug logging + icon fix

