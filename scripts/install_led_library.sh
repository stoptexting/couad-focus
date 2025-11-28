#!/bin/bash
#
# RGB LED Matrix Library Installation Script
# Automatically compiles and installs the rpi-rgb-led-matrix library for 64x64 HUB75E panels
#
# Usage: bash scripts/install_led_library.sh
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LIBRARY_PATH="$PROJECT_ROOT/external/rpi-rgb-led-matrix"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}RGB LED Matrix Library Installer${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if running on Raspberry Pi
echo -e "${YELLOW}Checking platform...${NC}"
ARCH=$(uname -m)
OS=$(uname -s)

if [[ "$OS" != "Linux" ]]; then
    echo -e "${RED}ERROR: This script must be run on Linux (Raspberry Pi)${NC}"
    echo -e "${RED}Current OS: $OS${NC}"
    exit 1
fi

if [[ ! "$ARCH" =~ ^(armv7l|aarch64|armv6l)$ ]]; then
    echo -e "${YELLOW}WARNING: This script is designed for Raspberry Pi (ARM)${NC}"
    echo -e "${YELLOW}Detected architecture: $ARCH${NC}"
    echo -e "${YELLOW}Proceeding anyway, but library may not work correctly...${NC}"
    sleep 2
fi

echo -e "${GREEN}Platform: $OS $ARCH ✓${NC}"
echo ""

# Check if library directory exists
if [ ! -d "$LIBRARY_PATH" ]; then
    echo -e "${RED}ERROR: Library not found at $LIBRARY_PATH${NC}"
    echo -e "${RED}Please ensure you've cloned the repository correctly${NC}"
    exit 1
fi

echo -e "${GREEN}Library source found at: $LIBRARY_PATH ✓${NC}"
echo ""

# Check if already installed
echo -e "${YELLOW}Checking if rgbmatrix is already installed...${NC}"
if python3 -c "import rgbmatrix" 2>/dev/null; then
    echo -e "${GREEN}rgbmatrix module is already installed!${NC}"
    echo -e "${YELLOW}Do you want to reinstall? This will rebuild and reinstall the library.${NC}"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Installation cancelled${NC}"
        exit 0
    fi
fi

# Update package lists
echo -e "${YELLOW}Updating package lists...${NC}"
sudo apt-get update -qq || {
    echo -e "${RED}Failed to update package lists${NC}"
    exit 1
}
echo -e "${GREEN}Package lists updated ✓${NC}"
echo ""

# Install build dependencies
echo -e "${YELLOW}Installing build dependencies...${NC}"
echo -e "${BLUE}This may take a few minutes on first install...${NC}"

DEPENDENCIES=(
    "python3-dev"
    "python3-pip"
    "cython3"
    "gcc"
    "g++"
    "make"
    "git"
)

for dep in "${DEPENDENCIES[@]}"; do
    if dpkg -l | grep -q "^ii  $dep "; then
        echo -e "  ${GREEN}✓${NC} $dep (already installed)"
    else
        echo -e "  ${YELLOW}Installing $dep...${NC}"
        sudo apt-get install -y "$dep" -qq || {
            echo -e "${RED}Failed to install $dep${NC}"
            exit 1
        }
        echo -e "  ${GREEN}✓${NC} $dep"
    fi
done

echo -e "${GREEN}All dependencies installed ✓${NC}"
echo ""

# Navigate to library directory
cd "$LIBRARY_PATH"

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
make -C lib clean 2>/dev/null || true
cd bindings/python
make clean 2>/dev/null || true
rm -rf build/ rgbmatrix.egg-info/ 2>/dev/null || true
cd "$LIBRARY_PATH"
echo -e "${GREEN}Clean complete ✓${NC}"
echo ""

# Build the C++ library
echo -e "${YELLOW}Building C++ library...${NC}"
echo -e "${BLUE}This will take 2-5 minutes depending on your Raspberry Pi model...${NC}"

make -C lib -j$(nproc) || {
    echo -e "${RED}Failed to build C++ library${NC}"
    echo -e "${RED}Check the error messages above${NC}"
    exit 1
}

echo -e "${GREEN}C++ library built successfully ✓${NC}"
echo ""

# Build and install Python bindings
echo -e "${YELLOW}Building Python bindings...${NC}"
echo -e "${BLUE}Compiling Cython extensions...${NC}"

PYTHON_BIN=$(which python3)
make build-python PYTHON="$PYTHON_BIN" || {
    echo -e "${RED}Failed to build Python bindings${NC}"
    echo -e "${RED}Check the error messages above${NC}"
    exit 1
}

echo -e "${GREEN}Python bindings built successfully ✓${NC}"
echo ""

# Install Python module
echo -e "${YELLOW}Installing Python module (requires sudo)...${NC}"
sudo make install-python PYTHON="$PYTHON_BIN" || {
    echo -e "${RED}Failed to install Python module${NC}"
    exit 1
}

echo -e "${GREEN}Python module installed ✓${NC}"
echo ""

# Verify installation
echo -e "${YELLOW}Verifying installation...${NC}"

if python3 -c "import rgbmatrix; print('Import successful')" 2>/dev/null; then
    echo -e "${GREEN}✓ rgbmatrix module can be imported${NC}"

    # Try to import specific classes
    if python3 -c "from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics; print('Classes imported successfully')" 2>/dev/null; then
        echo -e "${GREEN}✓ All required classes available${NC}"
    else
        echo -e "${YELLOW}WARNING: Could not import all classes${NC}"
    fi
else
    echo -e "${RED}ERROR: Installation completed but module cannot be imported${NC}"
    echo -e "${RED}This may indicate a problem with the installation${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Installation Complete! ✓${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Ensure your 64x64 RGB LED matrix is properly wired"
echo -e "  2. Run the LED manager: ${YELLOW}python3 shared/led_manager/led_manager_daemon.py${NC}"
echo -e "  3. Check for any hardware errors in the output"
echo ""
echo -e "${BLUE}Troubleshooting:${NC}"
echo -e "  - If you see flickering, try adjusting gpio_slowdown in config.py"
echo -e "  - The program requires root or GPIO permissions to run"
echo -e "  - Disable onboard audio if you get audio-related errors"
echo ""
echo -e "${GREEN}Installation log saved to: /tmp/led_install.log${NC}"

# Save installation info
{
    echo "Installation completed: $(date)"
    echo "Architecture: $ARCH"
    echo "Python: $PYTHON_BIN"
    python3 -c "import rgbmatrix; print('rgbmatrix version: OK')"
} > /tmp/led_install.log 2>&1

exit 0
