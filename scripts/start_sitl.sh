#!/bin/bash
# ============================================================
# start_sitl.sh — Entrypoint for ArduPilot SITL container
# Launches ArduCopter simulator on TCP port 5760
# ============================================================

set -e

echo "========================================="
echo " Starting ArduPilot SITL (ArduCopter)"
echo "========================================="

cd /ardupilot

# Use sim_vehicle.py to launch ArduCopter SITL
# --no-mavproxy : don't start MAVProxy (we connect externally)
# -j4           : parallel build threads (already built, but needed by script)
# --map/--console are intentionally NOT used (headless mode)
# Output to TCP port 5760 for external connections

python3 Tools/autotest/sim_vehicle.py \
    -v ArduCopter \
    --no-rebuild \
    --no-mavproxy \
    -w \
    --out "tcpin:0.0.0.0:5760" \
    --speedup 5 \
    2>&1 &

SITL_PID=$!

echo "SITL PID: $SITL_PID"
echo "Waiting for SITL to be ready on port 5760..."

# Wait for TCP port 5760 to be available (max 120 seconds)
TIMEOUT=120
ELAPSED=0
while ! python3 -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('localhost',5760)); s.close()" 2>/dev/null; do
    sleep 2
    ELAPSED=$((ELAPSED + 2))
    if [ $ELAPSED -ge $TIMEOUT ]; then
        echo "ERROR: SITL did not start within ${TIMEOUT}s"
        exit 1
    fi
    echo "  ... waiting (${ELAPSED}s / ${TIMEOUT}s)"
done

echo "========================================="
echo " SITL is READY on tcp:0.0.0.0:5760"
echo "========================================="

# Keep container running by waiting on the SITL process
wait $SITL_PID
