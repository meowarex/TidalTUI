#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🎵 Starting TIDAL TUI Setup...${NC}"

# Check if Python dependencies are installed
if ! command -v pip &> /dev/null; then
    echo -e "${RED}Python pip is not installed!${NC}"
    echo "Please install Python and pip first."
    exit 1
fi

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install --break-system-packages -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Starting TIDAL TUI...${NC}"
    python src/tidal_tui.py
else
    echo -e "${RED}Failed to install dependencies! Please check the errors above.${NC}"
    exit 1
fi 