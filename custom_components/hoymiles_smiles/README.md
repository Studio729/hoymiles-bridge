# Hoymiles MQTT Bridge - Custom Integration

## 🎉 Native Home Assistant Integration

This is a **custom Home Assistant integration** for monitoring your Hoymiles MQTT Bridge application. It provides a native, UI-based configuration experience following [Home Assistant Core development standards](https://developers.home-assistant.io/docs/development_index/).

---

## ✨ Features

- ✅ **UI-Based Configuration** - No YAML editing required
- ✅ **Device Registry Integration** - All entities grouped under one device
- ✅ **8 Sensor Entities** - Comprehensive monitoring
- ✅ **1 Binary Sensor** - Health status (on/off)
- ✅ **Configurable Scan Interval** - Adjust via UI
- ✅ **Automatic Updates** - DataUpdateCoordinator optimization
- ✅ **Rich Attributes** - Additional data on each entity
- ✅ **Diagnostic Sensors** - Database stats
- ✅ **Custom Branding** - Hoymiles icon and logo (v1.1)
- ✅ **Enhanced Reliability** - Persistent HTTP sessions and auto-retry (v1.1)

---

## 📦 What's Included

### Sensors (8 entities)

1. **Uptime** - Application uptime in seconds
2. **MQTT Messages Published** - Total MQTT messages sent
3. **MQTT Errors** - Total MQTT errors
4. **DTU Query Count** - Total DTU queries executed
5. **DTU Error Count** - Total DTU errors
6. **DTU Last Query** - Seconds since last successful query
7. **Database Size** (diagnostic) - SQLite database size (MB)
8. **Cached Records** (diagnostic) - Number of cached records

### Binary Sensors (1 entity)

1. **Application Healthy** - Overall health status with rich attributes

### Device

All entities are grouped under:
- **Device Name**: Hoymiles MQTT Bridge
- **Manufacturer**: Hoymiles
- **Model**: MQTT Bridge
- **Software Version**: 0.12.0

---

## 🚀 Quick Start

### 1. Install

Copy this folder to your Home Assistant `custom_components` directory:

```bash
cp -r hoymiles_smiles/ /config/custom_components/
```

### 2. Restart Home Assistant

```
Settings → System → Restart
```

### 3. Add Integration

1. Go to **Settings → Devices & Services**
2. Click **+ ADD INTEGRATION**
3. Search for **"Hoymiles MQTT Bridge"**
4. Enter your host and port
5. Click **Submit**

✅ Done!

---

## 📋 Requirements

- Home Assistant 2024.2 or newer
- Hoymiles MQTT application with health endpoint enabled
- Health API accessible from Home Assistant

---

## ⚙️ Configuration

### Initial Setup

| Field | Description | Example |
|-------|-------------|---------|
| Host | IP address of Hoymiles MQTT | `192.168.1.31` |
| Port | Health API port | `8090` |

### Options

After installation, click **CONFIGURE** to adjust:

| Option | Default | Range |
|--------|---------|-------|
| Scan Interval (seconds) | 60 | 10-300 |

---

## 📊 Entity IDs

Entities follow this naming convention:

```
sensor.hoymiles_smiles_bridge_uptime
sensor.hoymiles_smiles_bridge_mqtt_messages_published
sensor.hoymiles_smiles_bridge_mqtt_errors
sensor.hoymiles_smiles_bridge_dtu_query_count
sensor.hoymiles_smiles_bridge_dtu_error_count
sensor.hoymiles_smiles_bridge_dtu_last_query
sensor.hoymiles_smiles_bridge_database_size
sensor.hoymiles_smiles_bridge_cached_records
binary_sensor.hoymiles_smiles_bridge_application_healthy
```

---

## 🎨 Example Dashboard

```yaml
type: entities
title: Hoymiles MQTT Bridge
entities:
  - entity: binary_sensor.hoymiles_smiles_bridge_application_healthy
  - entity: sensor.hoymiles_smiles_bridge_uptime
  - entity: sensor.hoymiles_smiles_bridge_dtu_last_query
  - entity: sensor.hoymiles_smiles_bridge_mqtt_messages_published
  - entity: sensor.hoymiles_smiles_bridge_mqtt_errors
```

---

## 🔧 Troubleshooting

### "Cannot connect" during setup

**Check:**
1. Verify API is accessible: `curl http://HOST:PORT/health`
2. Ensure health server is running in Hoymiles MQTT
3. Check `HEALTH_ENABLED: true` in docker-compose.yml

### Sensors show "unavailable"

**Check:**
1. Home Assistant logs: Settings → System → Logs
2. Filter for "hoymiles_smiles"
3. Verify API endpoints are responding

### Intermittent "unavailable" status (Fixed in v1.1)

If you're using v1.0 and experiencing intermittent unavailability every 30-40 minutes:
- **Solution**: Upgrade to v1.1 which includes persistent HTTP sessions, automatic retries, and increased timeout resilience
- **Details**: See `INTEGRATION_IMPROVEMENTS_v1.1.md` in the project root

---

## 📚 Documentation

- **Installation Guide**: `CUSTOM_INTEGRATION_INSTALL.md`
- **Developer Guide**: `CUSTOM_INTEGRATION_GUIDE.md`
- **Comparison**: `INTEGRATION_COMPARISON.md`

---

## 🔗 Links

- **Home Assistant Dev Docs**: https://developers.home-assistant.io/
- **Health API Config**: See `WEB_SERVER_CONFIG.md` in project root

---

## 📝 Version

**Current Version**: 1.1.0

**Compatibility**: Home Assistant 2024.2+

### Version History
- **v1.1.0** (2024-11-05): Enhanced reliability with persistent HTTP sessions, auto-retry logic, and custom branding
- **v1.0.0** (2024-11-04): Initial release

---

## ✅ Features Checklist

- [x] UI-based configuration (config flow)
- [x] Options flow for runtime configuration
- [x] DataUpdateCoordinator for efficient polling
- [x] Device registry integration
- [x] Entity registry with unique IDs
- [x] Proper availability handling
- [x] Rich state attributes
- [x] Diagnostic entities
- [x] Error handling and logging
- [x] Translations support (English)
- [x] Custom icon and logo (v1.1)
- [x] Persistent HTTP sessions (v1.1)
- [x] Automatic retry with exponential backoff (v1.1)
- [x] Enhanced timeout handling (v1.1)
- [x] Resource cleanup on unload (v1.1)
- [ ] Services (future)
- [ ] Diagnostics download (future)
- [ ] Multiple DTU support (future)

---

## 🎉 Summary

This custom integration provides a **native Home Assistant experience** for monitoring your Hoymiles MQTT Bridge. No YAML configuration needed - just add through the UI and start monitoring!

**Enjoy! 🚀**

