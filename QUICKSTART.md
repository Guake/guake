# Guake Quick Start Guide

## 🚀 One-Command Setup

### Option 1: Automated Setup (Recommended)
```bash
cd ~/Documents/GitHub/guake
./scripts/setup-dev.sh
```

### Option 2: Manual Setup
```bash
cd ~/Documents/GitHub/guake

# Install dependencies
pip install pipenv
make dev

# Install schemas (required even for local dev)
sudo make install-schemas

# Done! Now you can run tests or build
```

## 📦 Running & Testing

### Run Tests
```bash
make test
```

### Run in Development Mode (requires X11/Linux)
```bash
make run
```

### Build Distribution Packages
```bash
make build
```

### Code Quality Checks
```bash
make style      # All style checks (black, flake8, pylint)
make black      # Auto-format code
```

## 🐳 Docker Setup (Easiest for GUI Testing)

### Build Docker Image
```bash
docker build -t guake:dev -f Dockerfile.dev .
```

### Run with Docker Compose
```bash
docker-compose -f docker-compose.dev.yml up
```

### Or Run Manually
```bash
# Linux with X11
docker run -it --rm \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -e DISPLAY=$DISPLAY \
  guake:dev /bin/bash

# Inside container:
guake &
```

## 📋 Common Tasks

### Install in editable mode
```bash
pip install -e .
```

### Run specific tests
```bash
make test  # Run all tests
pytest guake/tests/test_boxes.py  # Run specific test file
```

### Format code
```bash
make black
```

### Check for errors (no formatting)
```bash
make black-check
make flake8
make pylint
```

### Clean everything
```bash
make clean
```

### Uninstall from system
```bash
sudo make uninstall
```

## 🔧 Troubleshooting

### Pipenv lock issues
```bash
make clean
make dev PYTHON_INTERPRETER=python3
```

### "Permission denied" on schema installation
```bash
# Make sure you use sudo
sudo make install-schemas
```

### Docker can't find display
```bash
# First, make sure X11 socket exists:
ls /tmp/.X11-unix/

# Then run docker with DISPLAY variable
docker run -e DISPLAY=$DISPLAY guake:dev
```

## 📚 More Information

- Full setup guide: [SETUP_DEV.md](SETUP_DEV.md)
- Contributing guidelines: [docs/source/contributing/](docs/source/contributing/)
- Issue tracker: https://github.com/guake/guake/issues

## 🎯 Project Layout

```
guake/
├── guake/              # Main source code
│   ├── __init__.py
│   ├── callbacks.py
│   ├── boxes.py
│   └── ...
├── guake/data/         # UI definitions, images, schemas
├── po/                 # Translations
├── scripts/            # Helper scripts
├── tests/              # Test suite
├── Makefile            # Build commands
├── setup.py            # Package setup
└── Dockerfile.dev      # Docker image definition
```

## ✅ Quick Health Check

```bash
# Verify setup is working:
python3 -c "import guake; print('✓ Guake imports successfully')"
make test  # Should pass
make style # Should have no errors
```

---

**Next**: Run `./scripts/setup-dev.sh` to get started!
