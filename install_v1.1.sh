#!/bin/bash
#
# Installation Script for Hoymiles MQTT Custom Integration v1.1
# 
# This script installs/updates the custom Home Assistant integration
# with enhanced reliability and custom branding.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default Home Assistant config directory
HA_CONFIG_DIR="${HA_CONFIG_DIR:-/config}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Hoymiles MQTT Custom Integration v1.1 Installer         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running from correct directory
if [ ! -d "custom_components/hoymiles_smiles" ]; then
    echo -e "${RED}Error: custom_components/hoymiles_smiles directory not found${NC}"
    echo -e "${YELLOW}Please run this script from the hoymiles-smiles-main directory${NC}"
    exit 1
fi

# Check if HA config directory exists
if [ ! -d "$HA_CONFIG_DIR" ]; then
    echo -e "${YELLOW}Home Assistant config directory not found at: $HA_CONFIG_DIR${NC}"
    echo -n "Enter your Home Assistant config directory path: "
    read -r HA_CONFIG_DIR
    
    if [ ! -d "$HA_CONFIG_DIR" ]; then
        echo -e "${RED}Error: Directory $HA_CONFIG_DIR does not exist${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓${NC} Home Assistant config directory: ${BLUE}$HA_CONFIG_DIR${NC}"

# Create custom_components directory if it doesn't exist
CUSTOM_COMPONENTS_DIR="$HA_CONFIG_DIR/custom_components"
if [ ! -d "$CUSTOM_COMPONENTS_DIR" ]; then
    echo -e "${YELLOW}Creating custom_components directory...${NC}"
    mkdir -p "$CUSTOM_COMPONENTS_DIR"
fi

# Backup existing installation if it exists
TARGET_DIR="$CUSTOM_COMPONENTS_DIR/hoymiles_smiles"
if [ -d "$TARGET_DIR" ]; then
    BACKUP_DIR="${TARGET_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${YELLOW}Backing up existing installation to: ${BACKUP_DIR}${NC}"
    cp -r "$TARGET_DIR" "$BACKUP_DIR"
    echo -e "${GREEN}✓${NC} Backup created"
fi

# Copy the integration
echo -e "${BLUE}Installing Hoymiles MQTT Custom Integration v1.1...${NC}"
cp -r custom_components/hoymiles_smiles "$CUSTOM_COMPONENTS_DIR/"

# Verify installation
if [ ! -f "$TARGET_DIR/manifest.json" ]; then
    echo -e "${RED}Error: Installation failed - manifest.json not found${NC}"
    exit 1
fi

# Check version
VERSION=$(grep '"version"' "$TARGET_DIR/manifest.json" | sed 's/.*: "\(.*\)".*/\1/')
echo -e "${GREEN}✓${NC} Installed version: ${GREEN}$VERSION${NC}"

# Verify icons
if [ -f "$TARGET_DIR/icon.png" ] && [ -f "$TARGET_DIR/logo.png" ]; then
    ICON_SIZE=$(du -h "$TARGET_DIR/icon.png" | cut -f1)
    LOGO_SIZE=$(du -h "$TARGET_DIR/logo.png" | cut -f1)
    echo -e "${GREEN}✓${NC} Icon installed: ${ICON_SIZE}"
    echo -e "${GREEN}✓${NC} Logo installed: ${LOGO_SIZE}"
else
    echo -e "${YELLOW}⚠${NC} Warning: Icon or logo not found"
fi

# List all installed files
echo ""
echo -e "${BLUE}Installed files:${NC}"
ls -lh "$TARGET_DIR" | tail -n +2 | awk '{printf "  %s %-8s %s\n", $9, $5, ($9 ~ /\.png$/ ? "← Asset" : "")}'

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Installation Complete!                                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. Restart Home Assistant"
echo -e "     ${BLUE}Settings → System → Restart${NC}"
echo -e ""
echo -e "  2. Verify the integration loaded"
echo -e "     ${BLUE}Settings → Devices & Services → Hoymiles MQTT Bridge${NC}"
echo -e ""
echo -e "  3. Check for the custom icon"
echo -e "     ${BLUE}Look for the Hoymiles icon on the integration tile${NC}"
echo -e ""
echo -e "  4. Monitor for 24 hours"
echo -e "     ${BLUE}Verify no intermittent 'unavailable' status${NC}"
echo -e ""
echo -e "${YELLOW}Documentation:${NC}"
echo -e "  • ${BLUE}UPGRADE_TO_v1.1_SUMMARY.md${NC} - What's new and how to test"
echo -e "  • ${BLUE}INTEGRATION_IMPROVEMENTS_v1.1.md${NC} - Technical details"
echo -e "  • ${BLUE}INTEGRATION_QUICK_FIX_GUIDE.md${NC} - Quick reference"
echo -e ""
echo -e "${GREEN}Enjoy your stable, reliable monitoring! 🚀${NC}"
echo ""

# Offer to restart HA if ha command is available
if command -v ha &> /dev/null; then
    echo -n "Would you like to restart Home Assistant now? (y/N): "
    read -r RESTART
    if [ "$RESTART" = "y" ] || [ "$RESTART" = "Y" ]; then
        echo -e "${BLUE}Restarting Home Assistant...${NC}"
        ha core restart
        echo -e "${GREEN}✓${NC} Restart initiated"
    else
        echo -e "${YELLOW}Remember to restart Home Assistant manually!${NC}"
    fi
else
    echo -e "${YELLOW}Note: Please restart Home Assistant manually${NC}"
fi

echo ""

