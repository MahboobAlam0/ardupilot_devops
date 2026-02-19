# ============================================================
# ArduPilot SITL Docker Image
# Purpose: Reproducible build of ArduCopter simulator for CI
# ============================================================
FROM ubuntu:22.04

LABEL maintainer="ArduPilot DevOps Project"
LABEL description="ArduPilot SITL (ArduCopter) for CI/CD pipeline testing"

# Prevent interactive prompts during package install
ENV DEBIAN_FRONTEND=noninteractive

# ---- 1. Install system dependencies ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    sudo \
    lsb-release \
    software-properties-common \
    python3 \
    python3-pip \
    python3-dev \
    python3-setuptools \
    python3-wheel \
    python3-matplotlib \
    python3-serial \
    python3-scipy \
    python3-opencv \
    python3-numpy \
    python3-pyparsing \
    python3-wxgtk4.0 \
    python-is-python3 \
    libxml2-dev \
    libxslt1-dev \
    build-essential \
    ccache \
    g++ \
    gawk \
    wget \
    && rm -rf /var/lib/apt/lists/*

# ---- 2. Clone ArduPilot (specific tag for reproducibility) ----
WORKDIR /ardupilot
RUN git clone --recurse-submodules --depth 1 --branch Copter-4.5.7 \
    https://github.com/ArduPilot/ardupilot.git .

# ---- 3. Install ArduPilot Python dependencies ----
RUN pip3 install --no-cache-dir \
    future \
    empy==3.3.4 \
    pexpect \
    dronekit \
    MAVProxy \
    pymavlink

# ---- 4. Build ArduCopter SITL binary ----
RUN ./waf configure --board sitl \
    && ./waf copter

# ---- 5. Copy entrypoint script ----
COPY scripts/start_sitl.sh /ardupilot/start_sitl.sh
RUN chmod +x /ardupilot/start_sitl.sh

# ---- 6. Expose MAVLink ports ----
# 5760: primary MAVLink TCP port used by SITL
EXPOSE 5760

# ---- 7. Health check: verify SITL is accepting connections ----
HEALTHCHECK --interval=10s --timeout=5s --start-period=60s --retries=6 \
    CMD python3 -c "import socket; s=socket.socket(); s.settimeout(3); s.connect(('localhost',5760)); s.close()" || exit 1

# ---- 8. Entrypoint ----
ENTRYPOINT ["/ardupilot/start_sitl.sh"]
