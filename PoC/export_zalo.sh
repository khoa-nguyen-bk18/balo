#!/usr/bin/env bash
# ==============================================================================
# Zalo Data Exporter for Non-Root Android (via ADB)
# Targets: vivo / Android 11+ / Scoped Storage & Public Media
# ==============================================================================

set -eo pipefail

BACKUP_DIR="${1:-./zalo_backup}"
DEVICE_ID=""

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}         Zalo Non-Root Data Exporter (ADB)            ${NC}"
echo -e "${CYAN}======================================================${NC}"

# Check ADB installation
if ! command -v adb &>/dev/null; then
    echo -e "${RED}[!] Error: 'adb' command not found. Please install Android Platform Tools.${NC}"
    exit 1
fi

# Check connected device
DEVICES_COUNT=$(adb devices | grep -v "List" | grep -w "device" | wc -l | tr -d ' ')
if [ "$DEVICES_COUNT" -eq 0 ]; then
    echo -e "${RED}[!] Error: No authorized Android device found.${NC}"
    echo -e "    Please connect your phone, enable USB Debugging, and authorize this Mac."
    exit 1
elif [ "$DEVICES_COUNT" -gt 1 ]; then
    echo -e "${YELLOW}[!] Multiple devices found. Using the first available:${NC}"
    DEVICE_ID=$(adb devices | grep -v "List" | grep -w "device" | head -n 1 | awk '{print $1}')
    echo -e "    Target Device ID: ${DEVICE_ID}"
    ADB_CMD="adb -s ${DEVICE_ID}"
else
    DEVICE_ID=$(adb devices | grep -v "List" | grep -w "device" | awk '{print $1}')
    echo -e "${GREEN}[✓] Device Connected: ${DEVICE_ID}${NC}"
    ADB_CMD="adb -s ${DEVICE_ID}"
fi

# Retrieve device metadata
DEVICE_MODEL=$(${ADB_CMD} shell getprop ro.product.model | tr -d '\r')
DEVICE_BRAND=$(${ADB_CMD} shell getprop ro.product.manufacturer | tr -d '\r')
ANDROID_VER=$(${ADB_CMD} shell getprop ro.build.version.release | tr -d '\r')

echo -e "    Model: ${DEVICE_BRAND} ${DEVICE_MODEL} (Android ${ANDROID_VER})"
echo ""

# Scan available Zalo storage on device
echo -e "${BLUE}[*] Scanning Zalo storage on device...${NC}"
SCOPED_PATH="/sdcard/Android/data/com.zing.zalo/files/zalo"
CACHE_PATH="/sdcard/Android/data/com.zing.zalo/cache/zalo"
PUB_DOWNLOAD="/sdcard/Download/Zalo"
PUB_PICTURES="/sdcard/Pictures/Zalo"

SIZE_PICTURES=$(${ADB_CMD} shell "du -sh ${SCOPED_PATH}/picture 2>/dev/null | awk '{print \$1}'" | tr -d '\r' || echo "0")
SIZE_DOWNLOADS=$(${ADB_CMD} shell "du -sh ${SCOPED_PATH}/downloads 2>/dev/null | awk '{print \$1}'" | tr -d '\r' || echo "0")
SIZE_VOICE=$(${ADB_CMD} shell "du -sh ${SCOPED_PATH}/voice 2>/dev/null | awk '{print \$1}'" | tr -d '\r' || echo "0")
SIZE_VIDEO=$(${ADB_CMD} shell "du -sh ${SCOPED_PATH}/video 2>/dev/null | awk '{print \$1}'" | tr -d '\r' || echo "0")
SIZE_PUB_DL=$(${ADB_CMD} shell "du -sh ${PUB_DOWNLOAD} 2>/dev/null | awk '{print \$1}'" | tr -d '\r' || echo "0")
SIZE_PUB_PIC=$(${ADB_CMD} shell "du -sh ${PUB_PICTURES} 2>/dev/null | awk '{print \$1}'" | tr -d '\r' || echo "0")
SIZE_CACHE=$(${ADB_CMD} shell "du -sh ${CACHE_PATH} 2>/dev/null | awk '{print \$1}'" | tr -d '\r' || echo "0")

echo -e "    - Chat Pictures (Scoped):      ${CYAN}${SIZE_PICTURES}${NC}"
echo -e "    - Chat Downloads (Scoped):     ${CYAN}${SIZE_DOWNLOADS}${NC}"
echo -e "    - Voice Memos (Scoped):        ${CYAN}${SIZE_VOICE}${NC}"
echo -e "    - Public Downloads:            ${CYAN}${SIZE_PUB_DL}${NC}"
echo -e "    - Public Pictures Album:       ${CYAN}${SIZE_PUB_PIC}${NC}"
echo -e "    - Videos (Scoped):             ${CYAN}${SIZE_VIDEO}${NC}"
echo -e "    - Image/Video Cache:           ${CYAN}${SIZE_CACHE}${NC}"
echo ""

# Check local disk space
FREE_DISK_MB=$(df -m . | awk 'NR==2 {print $4}')
FREE_DISK_GB=$(awk "BEGIN {printf \"%.1f\", ${FREE_DISK_MB}/1024}")
echo -e "${BLUE}[*] Local Mac Free Space: ${GREEN}${FREE_DISK_GB} GB${NC}"
echo -e "    Destination Folder:    ${YELLOW}${BACKUP_DIR}${NC}"
echo ""

# Present Menu
echo -e "Select export profile:"
echo -e "  ${GREEN}1)${NC} ${BOLD}Essential Media${NC} (Pictures, Downloads, Voice, Public Albums) ~ 1 GB ${YELLOW}[Recommended]${NC}"
echo -e "  ${GREEN}2)${NC} ${BOLD}Complete Media${NC} (Includes Videos & Large Files) ~ 6.5 GB"
echo -e "  ${GREEN}3)${NC} ${BOLD}Everything + Cache${NC} (All files + cacheimg/video cache) ~ 7 GB"
echo -e "  ${GREEN}4)${NC} ${BOLD}Custom selection${NC}"
echo ""

read -rp "Enter option [1-4] (default: 1): " CHOICE
CHOICE="${CHOICE:-1}"

# Ensure output directory exists
mkdir -p "${BACKUP_DIR}"

pull_folder() {
    local src="$1"
    local dest_subfolder="$2"
    local desc="$3"

    local target_dir="${BACKUP_DIR}/${dest_subfolder}"
    mkdir -p "${target_dir}"

    echo -e "${BLUE}--> Pulling ${desc} from ${src}...${NC}"
    if ${ADB_CMD} shell "[ -e \"${src}\" ]" 2>/dev/null; then
        ${ADB_CMD} pull "${src}/." "${target_dir}/" || {
            echo -e "${YELLOW}[!] Warning: Some files could not be copied or directory was busy.${NC}"
        }
        echo -e "${GREEN}[✓] Finished: ${desc}${NC}"
    else
        echo -e "${YELLOW}[-] Skipped (path not found on device): ${src}${NC}"
    fi
}

START_TIME=$(date +%s)

case "$CHOICE" in
    1)
        echo -e "\n${GREEN}[*] Starting Essential Media Export...${NC}"
        pull_folder "${SCOPED_PATH}/picture" "chat_pictures" "Chat Pictures"
        pull_folder "${SCOPED_PATH}/downloads" "chat_downloads" "Chat Downloads"
        pull_folder "${SCOPED_PATH}/voice" "chat_voice_memos" "Voice Memos"
        pull_folder "${PUB_DOWNLOAD}" "public_downloads" "Public Downloads"
        pull_folder "${PUB_PICTURES}" "public_pictures" "Public Saved Pictures"
        pull_folder "${SCOPED_PATH}/recommend_link" "link_previews" "Shared Link Metadata"
        ;;
    2)
        echo -e "\n${GREEN}[*] Starting Complete Media Export...${NC}"
        pull_folder "${SCOPED_PATH}/picture" "chat_pictures" "Chat Pictures"
        pull_folder "${SCOPED_PATH}/downloads" "chat_downloads" "Chat Downloads"
        pull_folder "${SCOPED_PATH}/voice" "chat_voice_memos" "Voice Memos"
        pull_folder "${PUB_DOWNLOAD}" "public_downloads" "Public Downloads"
        pull_folder "${PUB_PICTURES}" "public_pictures" "Public Saved Pictures"
        pull_folder "${SCOPED_PATH}/video" "chat_videos" "Chat Videos"
        pull_folder "${SCOPED_PATH}/call_asr" "call_audio_asr" "Call Audio Logs"
        ;;
    3)
        echo -e "\n${GREEN}[*] Starting Full Export (+ Cache)...${NC}"
        pull_folder "${SCOPED_PATH}" "scoped_files_zalo" "Complete Scoped Storage (All Categories)"
        pull_folder "${PUB_DOWNLOAD}" "public_downloads" "Public Downloads"
        pull_folder "${PUB_PICTURES}" "public_pictures" "Public Saved Pictures"
        pull_folder "${CACHE_PATH}" "zalo_cache" "Zalo Image & Stream Cache"
        ;;
    4)
        echo -e "\nSelect categories to export (y/n):"
        read -rp "Pull Chat Pictures (${SIZE_PICTURES})? [y/n]: " P_PIC
        [[ "$P_PIC" =~ ^[Yy]$ ]] && pull_folder "${SCOPED_PATH}/picture" "chat_pictures" "Chat Pictures"

        read -rp "Pull Chat Downloads (${SIZE_DOWNLOADS})? [y/n]: " P_DL
        [[ "$P_DL" =~ ^[Yy]$ ]] && pull_folder "${SCOPED_PATH}/downloads" "chat_downloads" "Chat Downloads"

        read -rp "Pull Voice Memos (${SIZE_VOICE})? [y/n]: " P_VOICE
        [[ "$P_VOICE" =~ ^[Yy]$ ]] && pull_folder "${SCOPED_PATH}/voice" "chat_voice_memos" "Voice Memos"

        read -rp "Pull Public Downloads (${SIZE_PUB_DL})? [y/n]: " P_PDL
        [[ "$P_PDL" =~ ^[Yy]$ ]] && pull_folder "${PUB_DOWNLOAD}" "public_downloads" "Public Downloads"

        read -rp "Pull Public Pictures (${SIZE_PUB_PIC})? [y/n]: " P_PPIC
        [[ "$P_PPIC" =~ ^[Yy]$ ]] && pull_folder "${PUB_PICTURES}" "public_pictures" "Public Saved Pictures"

        read -rp "Pull Videos (${SIZE_VIDEO})? [y/n]: " P_VID
        [[ "$P_VID" =~ ^[Yy]$ ]] && pull_folder "${SCOPED_PATH}/video" "chat_videos" "Chat Videos"

        read -rp "Pull Image/Stream Cache (${SIZE_CACHE})? [y/n]: " P_CACHE
        [[ "$P_CACHE" =~ ^[Yy]$ ]] && pull_folder "${CACHE_PATH}" "zalo_cache" "Zalo Image & Stream Cache"
        ;;
    *)
        echo -e "${RED}[!] Invalid choice.${NC}"
        exit 1
        ;;
esac

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Generate export manifest
MANIFEST_FILE="${BACKUP_DIR}/export_manifest.txt"
cat <<EOF > "${MANIFEST_FILE}"
Zalo Data Export Manifest
=========================
Date: $(date)
Device: ${DEVICE_BRAND} ${DEVICE_MODEL} (Android ${ANDROID_VER})
Device Serial: ${DEVICE_ID}
Target Directory: $(cd "${BACKUP_DIR}" && pwd)
Duration: ${DURATION}s

Extracted Folders Summary:
$(du -sh "${BACKUP_DIR}"/* 2>/dev/null || true)

Total Size on Disk:
$(du -sh "${BACKUP_DIR}")
EOF

echo ""
echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}[✓] Export Completed Successfully in ${DURATION}s!${NC}"
echo -e "${GREEN}======================================================${NC}"
echo -e "All files saved to: ${CYAN}$(cd "${BACKUP_DIR}" && pwd)${NC}"
echo -e "Summary Manifest:   ${CYAN}${MANIFEST_FILE}${NC}"
echo ""
cat "${MANIFEST_FILE}"
