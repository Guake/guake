# Guake Docker Setup

Since Guake is a Linux GTK application, Docker provides the cleanest way to test and run it on macOS.

## Prerequisites

- Docker and Docker Compose installed
- For GUI testing: XQuartz (macOS) or X11 server (Linux)

## Quick Start

### 1. Build the Docker Image
```bash
docker build -t guake:dev -f Dockerfile.dev .
```

### 2. Using Docker Compose (Recommended)
```bash
docker-compose -f docker-compose.dev.yml up

# In another terminal, connect to the container:
docker exec -it guake-dev /bin/bash
```

### 3. Manual Docker Run

#### Linux Users:
```bash
docker run -it --rm \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -e DISPLAY=$DISPLAY \
  -v ${PWD}:/guake:rw \
  guake:dev /bin/bash
```

#### macOS Users:

First, install and start XQuartz:
```bash
brew install xquartz
open -a XQuartz
```

Configure X11 to accept connections from Docker:
```bash
defaults write org.macosforge.xquartz.X11 nolisten_tcp -boolean false
pkill -9 Xvfb; true
```

Then run Docker:
```bash
docker run -it --rm \
  -e DISPLAY=host.docker.internal:0 \
  -v ${PWD}:/guake:rw \
  guake:dev /bin/bash
```

Or use socat tunnel:
```bash
# Terminal 1: Start socat
brew install socat
socat TCP-LISTEN:6000,reuseaddr,fork UNIX-CONNECT:/tmp/.X11-unix/0 &

# Terminal 2: Run Docker
docker run -it --rm \
  -e DISPLAY=host.docker.internal:0 \
  -v ${PWD}:/guake:rw \
  guake:dev /bin/bash
```

## Inside the Container

### Setup (if not already done)
```bash
cd /guake
make dev
sudo make install-schemas
```

### Run Tests
```bash
make test
make test-coverage
```

### Check Code Quality
```bash
make style
make check
```

### Run Guake GUI
```bash
guake &
```

### Build Distribution
```bash
make build
```

### Access Python Shell
```bash
pipenv shell
python3 -c "import guake; print(guake.__version__)"
```

## Image Details

The `Dockerfile.dev` includes:

- **Base:** Ubuntu 22.04 LTS
- **GTK:** GTK 3.0 with VTE terminal widget
- **Tools:** Python 3, pipenv, git, build essentials
- **Locale:** Full locale support
- **D-Bus:** For system communication
- **Development:** All headers and dev libraries

## Common Issues

### "Cannot connect to X server"
- **Linux:** Make sure `/tmp/.X11-unix` exists and is accessible
- **macOS:** Ensure XQuartz is running and X11 forwarding is configured

### "No module named 'gi' (GObject introspection)"
The Dockerfile includes all necessary GObject introspection bindings. If still missing:
```bash
apt-get update && apt-get install -y python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91
```

### "dbus-launch cannot be run setuid"
This is normal in Docker. DBus operations should still work. Run:
```bash
export DBUS_SYSTEM_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket
```

### "Permission denied" errors
The container runs as root by default. For safer operation, modify the Dockerfile to create a non-root user.

## Customization

### Use Different Python Version
```bash
docker build -t guake:py39 --build-arg PYTHON_VERSION=3.9 -f Dockerfile.dev .
```

### Add More Tools to Container
Edit `Dockerfile.dev` and add to the `apt-get install` command.

### Persistent Container
```bash
docker run -d --name guake-dev \
  -e DISPLAY=$DISPLAY \
  -v ${PWD}:/guake:rw \
  guake:dev sleep infinity

# Connect whenever needed:
docker exec -it guake-dev /bin/bash
```

## Integration with macOS Development

### Mount Local Code
```bash
docker run -it --rm \
  -v ~/Documents/GitHub/guake:/guake:rw \
  guake:dev /bin/bash
```

### Use IDE on macOS, Test in Docker
1. Edit code in VS Code/PyCharm on macOS
2. Run tests in Docker:
```bash
docker exec -it guake-dev make test
```

### Access Built Packages from macOS
```bash
docker run -it --rm \
  -v ${PWD}/dist:/guake/dist \
  guake:dev bash -c "make build && ls -la dist/"
```

## Performance Notes

- First build: ~5 minutes (downloads and installs dependencies)
- Subsequent runs: < 1 second (cached layers)
- Image size: ~1.5 GB
- Container size: ~500 MB when running

## Resources

- Docker documentation: https://docs.docker.com/
- XQuartz (macOS): https://www.xquartz.org/
- GTK3 documentation: https://developer.gnome.org/gtk3/

---

For general development setup, see [SETUP_DEV.md](SETUP_DEV.md)
