#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
NC = '\033[0m'  # No Color

def print_colored(text, color):
    """Print colored text if supported"""
    if sys.platform == 'win32':
        print(text)
    else:
        print(f"{color}{text}{NC}")

def check_env_file():
    """Check if .env file exists and create if needed"""
    if not Path('.env').exists():
        print_colored("Error: .env file not found!", RED)
        print("Creating .env file...")
        token = input("Please enter your TIDAL API token: ")
        with open('.env', 'w') as f:
            f.write(f"TIDAL_TOKEN={token}\n")
        print_colored("Created .env file with your token", GREEN)

def check_dependencies():
    """Check if Python dependencies are installed"""
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print_colored("🎵 Starting TIDAL TUI Setup...", GREEN)

    # Check .env file
    check_env_file()

    # Install dependencies
    print_colored("Installing dependencies...", GREEN)
    if not check_dependencies():
        print_colored("Failed to install dependencies!", RED)
        sys.exit(1)

    # Run the application
    print_colored("Starting TIDAL TUI...", GREEN)
    subprocess.run([sys.executable, 'src/tidal_tui.py'])

if __name__ == "__main__":
    main() 