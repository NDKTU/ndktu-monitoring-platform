#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting installation of 'make'..."

# Check if running as root, if not, try using sudo
if [ "$EUID" -ne 0 ]; then
    SUDO="sudo"
else
    SUDO=""
fi

# Detect OS and use appropriate package manager
if command -v apt-get &> /dev/null; then
    echo "Detected Debian/Ubuntu-based system."
    $SUDO apt-get update
    $SUDO apt-get install -y make build-essential
elif command -v dnf &> /dev/null; then
    echo "Detected Fedora/RHEL-based system."
    $SUDO dnf install -y make automake gcc gcc-c++
elif command -v yum &> /dev/null; then
    echo "Detected older RHEL/CentOS-based system."
    $SUDO yum install -y make automake gcc gcc-c++
elif command -v pacman &> /dev/null; then
    echo "Detected Arch-based system."
    $SUDO pacman -Sy --noconfirm base-devel
elif command -v zypper &> /dev/null; then
    echo "Detected openSUSE-based system."
    $SUDO zypper install -y make gcc gcc-c++
elif command -v apk &> /dev/null; then
    echo "Detected Alpine Linux."
    $SUDO apk add make gcc g++ 
else
    echo "Unsupported or unrecognized Linux distribution."
    echo "Please install 'make' manually using your OS package manager."
    exit 1
fi

echo "----------------------------------------"
if command -v make &> /dev/null; then
    echo "Success! 'make' has been installed."
    make --version | head -n 1
else
    echo "Error: 'make' installation failed."
    exit 1
fi
