# Guake Development Setup Guide

## Quick Start

### 1. Development Environment (macOS)

While Guake runs on Linux with GTK/VTE, you can set up the development environment on macOS for contribution and testing:

```bash
cd ~/Documents/GitHub/guake

# Install Python dependencies
pip install pipenv
make dev

# Prepare for local execution
sudo make install-schemas

# Run tests
make test

# Build distribution
make build
```

### 2. Docker Setup (Recommended for Testing/Running)

Build and run Guake in a Linux container:

```bash
# Build the Docker image
docker build -t guake:dev -f Dockerfile.dev .

# Run Guake in container with X11 forwarding (Linux/Mac with XQuartz)
docker run -it --rm \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -e DISPLAY=$DISPLAY \
  guake:dev

# Or use Docker Compose for easier setup
docker-compose -f docker-compose.dev.yml up
```

## Installation Details

### macOS Development

**Prerequisites:**
- Python 3.6+
- pipenv
- For system-wide installation: sudo

**Steps:**

1. **Install dependencies via pipenv:**
   ```bash
   make dev
   ```
   This handles all Python dependencies automatically.

2. **Install GTK schemas (required even for local dev):**
   ```bash
   sudo make install-schemas
   ```

3. **Run without installation (dev mode):**
   ```bash
   make run
   ```

4. **Or install system-wide:**
   ```bash
   make dev && make && sudo make install
   ```

### Available Make Targets

| Target | Purpose |
|--------|---------|
| `make dev` | Setup complete dev environment |
| `make run` | Run Guake in development mode |
| `make test` | Run test suite |
| `make build` | Build distribution packages |
| `make style` | Run code style checks (black, flake8) |
| `make clean` | Clean all generated files |
| `make install` | Install system-wide (requires sudo) |
| `make uninstall` | Remove system installation |

### Docker Setup

Guake in Docker provides a clean Linux environment for testing.

**Quick start:**
```bash
docker build -t guake:dev -f Dockerfile.dev .
docker run -it --rm guake:dev /bin/bash
guake &  # Run in background
```

## Development Workflow

1. **Code changes:**
   ```bash
   # Edit files in ~/Documents/GitHub/guake/guake/
   ```

2. **Test changes:**
   ```bash
   make test          # Run unit tests
   make style         # Check code style
   make run           # Test GUI (requires X11 forwarding)
   ```

3. **Build distributions:**
   ```bash
   make build         # Creates wheel and sdist
   ```

## Troubleshooting

### Pipenv issues
```bash
# Clear and reinstall
make clean
make dev PYTHON_INTERPRETER=python3
```

### Schema compilation errors
```bash
# Reinstall schemas
sudo make uninstall-schemas
sudo make install-schemas
```

### Docker display issues (macOS)
```bash
# Install XQuartz first, then run with socat tunnel
brew install socat
socat TCP-LISTEN:6000,reuseaddr,fork UNIX-CONNECT:/tmp/.X11-unix/0 &
docker run -e DISPLAY=host.docker.internal:0 guake:dev
```

## Project Structure

```
guake/
├── guake/              # Main source code
├── po/                 # Translations
├── docs/               # Documentation
├── scripts/            # Helper scripts
├── Makefile            # Build automation
├── setup.py            # Python package setup
├── Dockerfile.dev      # Development container
└── docker-compose.dev.yml  # Docker Compose config
```

## Resources

- **Documentation:** `docs/source/contributing/dev_env.rst`
- **GitHub:** https://github.com/guake/guake
- **Issue Tracker:** https://github.com/guake/guake/issues
