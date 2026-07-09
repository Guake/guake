#!/bin/bash
set -e

# Guake Development Setup Script
# This script automates the setup of the development environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "================================================"
echo "Guake Development Environment Setup"
echo "================================================"
echo ""

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    echo "Detected macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    echo "Detected Linux"
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.6+"
    exit 1
fi
echo "✓ Python 3 found: $(python3 --version)"

# Check pipenv
if ! command -v pipenv &> /dev/null; then
    echo "⚠️  pipenv not found. Installing..."
    pip3 install pipenv
fi
echo "✓ pipenv found: $(pipenv --version)"

# Change to project directory
cd "$PROJECT_ROOT"

# Setup development environment
echo ""
echo "Installing dependencies..."
make dev

echo ""
echo "Preparing installation..."
make prepare-install

# Handle schema installation
echo ""
echo "Installing GTK schemas..."
if [[ "$OS" == "macos" ]]; then
    # macOS might need sudo
    if sudo -n true 2>/dev/null; then
        sudo make install-schemas
    else
        echo "⚠️  Schema installation requires sudo"
        echo "Run: sudo make install-schemas"
    fi
else
    # Linux
    if [ "$EUID" -eq 0 ]; then
        make install-schemas
    else
        echo "⚠️  Schema installation requires sudo"
        echo "Run: sudo make install-schemas"
    fi
fi

echo ""
echo "================================================"
echo "✓ Development setup complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Run tests:"
echo "   make test"
echo ""
echo "2. Check code style:"
echo "   make style"
echo ""
echo "3. Build distribution:"
echo "   make build"
echo ""
echo "4. Run locally (Linux/X11 required):"
echo "   make run"
echo ""
echo "5. Docker setup (recommended for testing):"
echo "   docker build -t guake:dev -f Dockerfile.dev ."
echo "   docker-compose -f docker-compose.dev.yml up"
echo ""
echo "For more details, see SETUP_DEV.md"
