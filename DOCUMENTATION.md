# Documentation Index

## Getting Started

| Document | Description | Time |
|----------|-------------|------|
| **[README.md](README.md)** | Project overview, features, quick examples | 5 min |
| **[QUICK_START.md](QUICK_START.md)** | 5-minute setup guide | 5 min |

---

## Configuration

| Document | Description |
|----------|-------------|
| **[WEB_SERVER_CONFIG.md](WEB_SERVER_CONFIG.md)** | Health endpoints, metrics, configuration |
| **[DOCKER_COMPOSE_GUIDE.md](DOCKER_COMPOSE_GUIDE.md)** | Docker Compose setup and profiles |
| **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** | Technical implementation details |

---

## Home Assistant

| Document | Description |
|----------|-------------|
| **[custom_components/hoymiles_mqtt/README.md](custom_components/hoymiles_mqtt/README.md)** | Custom integration overview |
| **[CUSTOM_INTEGRATION_INSTALL.md](CUSTOM_INTEGRATION_INSTALL.md)** | Detailed installation guide |
| **[CUSTOM_INTEGRATION_GUIDE.md](CUSTOM_INTEGRATION_GUIDE.md)** | Developer guide and architecture |
| **[HOME_ASSISTANT_SETUP.md](HOME_ASSISTANT_SETUP.md)** | YAML configuration setup |
| **[INTEGRATION_COMPARISON.md](INTEGRATION_COMPARISON.md)** | Custom vs YAML comparison |
| **[home_assistant_sensors.yaml](home_assistant_sensors.yaml)** | YAML sensor configuration |
| **[lovelace_dashboard.yaml](lovelace_dashboard.yaml)** | Dashboard configuration |

---

## Maintenance

| Document | Description |
|----------|-------------|
| **[UPGRADE_GUIDE.md](UPGRADE_GUIDE.md)** | Upgrading to v1.1 |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Problem solving and debugging |
| **[UPGRADE_v0.12.md](UPGRADE_v0.12.md)** | v0.12 migration guide |

---

## Project Information

| Document | Description |
|----------|-------------|
| **[CHANGELOG.md](CHANGELOG.md)** | Version history |
| **[CONTRIBUTING.md](CONTRIBUTING.md)** | Contribution guidelines |
| **[LICENSE](LICENSE)** | MIT License |

---

## Quick Reference

### I want to...

**Install for the first time**
→ [QUICK_START.md](QUICK_START.md)

**Add Home Assistant integration**
→ [custom_components/hoymiles_mqtt/README.md](custom_components/hoymiles_mqtt/README.md)  
→ Run: `./install_v1.1.sh`

**Upgrade to v1.1**
→ [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md)

**Fix issues**
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

**Configure Docker**
→ [DOCKER_COMPOSE_GUIDE.md](DOCKER_COMPOSE_GUIDE.md)

**Configure health endpoints**
→ [WEB_SERVER_CONFIG.md](WEB_SERVER_CONFIG.md)

**Set up YAML sensors**
→ [HOME_ASSISTANT_SETUP.md](HOME_ASSISTANT_SETUP.md)

**Compare integration methods**
→ [INTEGRATION_COMPARISON.md](INTEGRATION_COMPARISON.md)

**Understand the architecture**
→ [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

---

## Version Information

- **Application**: v0.12.0
- **Custom Integration**: v1.1.0
- **Python**: >= 3.10, < 3.14
- **Home Assistant**: >= 2024.2 (for custom integration)

---

## Essential Commands

```bash
# Quick install
./install_v1.1.sh

# Docker
docker-compose up -d
docker logs hoymiles_mqtt
docker restart hoymiles_mqtt

# Health check
curl http://localhost:8090/health | jq

# Troubleshoot
docker logs -f hoymiles_mqtt
```

---

## File Structure

```
hoymiles-mqtt-main/
├── README.md                          # Start here
├── DOCUMENTATION.md                   # This file
├── QUICK_START.md                     # 5-min setup
├── UPGRADE_GUIDE.md                   # v1.1 upgrade
├── TROUBLESHOOTING.md                 # Problem solving
│
├── custom_components/                 # Home Assistant integration
│   └── hoymiles_mqtt/
│       ├── README.md                  # Integration docs
│       ├── icon.png, logo.png         # Custom branding
│       └── *.py                       # Integration code
│
├── hoymiles_mqtt/                     # Application code
├── tests/                             # Test suite
├── docs/                              # MkDocs documentation
│
├── docker-compose.yml                 # Docker Compose
├── Dockerfile                         # Docker image
├── install_v1.1.sh                    # Install script
│
└── Configuration files:
    ├── home_assistant_sensors.yaml    # YAML sensors
    ├── lovelace_dashboard.yaml        # Dashboard
    └── config.yaml.example            # Config template
```

---

**Need help? Start with [README.md](README.md) or [QUICK_START.md](QUICK_START.md)**

