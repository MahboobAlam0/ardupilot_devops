"""
test_heartbeat.py — ArduPilot SITL Health Check Tests
=====================================================

These tests validate that the SITL simulator is running correctly
by checking MAVLink communication. This is the automated test
that runs in our CI pipeline.

What these tests prove:
  1. SITL is running and accepting MAVLink connections
  2. The vehicle is sending heartbeat messages
  3. The vehicle identifies as a quadrotor (ArduCopter)
"""

import pytest
import time
import sys
import os

# pymavlink setup — must set this BEFORE importing mavutil
os.environ["MAVLINK20"] = "1"

from pymavlink import mavutil


# ---- Configuration ----
SITL_CONNECTION = os.environ.get("SITL_CONNECTION", "tcp:localhost:5760")
HEARTBEAT_TIMEOUT = 30  # seconds to wait for first heartbeat
CONNECTION_RETRIES = 5   # number of connection attempts
RETRY_DELAY = 5          # seconds between retries


@pytest.fixture(scope="module")
def mavlink_connection():
    """
    Establish a MAVLink connection to SITL.
    Retries multiple times to handle SITL startup delay.
    """
    connection = None

    for attempt in range(1, CONNECTION_RETRIES + 1):
        try:
            print(f"\n[Attempt {attempt}/{CONNECTION_RETRIES}] "
                  f"Connecting to SITL at {SITL_CONNECTION}...")

            connection = mavutil.mavlink_connection(
                SITL_CONNECTION,
                source_system=255,
                source_component=0,
            )

            # Wait for the first heartbeat to confirm connection
            print(f"  Waiting up to {HEARTBEAT_TIMEOUT}s for heartbeat...")
            msg = connection.wait_heartbeat(timeout=HEARTBEAT_TIMEOUT)

            if msg:
                print(f"  ✅ Heartbeat received! "
                      f"(type={msg.type}, autopilot={msg.autopilot})")
                break
            else:
                print(f"  ⚠️ No heartbeat received, retrying...")
                connection.close()
                connection = None

        except Exception as e:
            print(f"  ❌ Connection failed: {e}")
            if connection:
                connection.close()
                connection = None
            time.sleep(RETRY_DELAY)

    if connection is None:
        pytest.fail(
            f"Could not connect to SITL at {SITL_CONNECTION} "
            f"after {CONNECTION_RETRIES} attempts"
        )

    yield connection

    # Teardown
    print("\nClosing MAVLink connection...")
    connection.close()


class TestSITLHeartbeat:
    """Test suite: Verify SITL is alive and responding correctly."""

    def test_heartbeat_received(self, mavlink_connection):
        """
        TEST 1: Verify that SITL sends a HEARTBEAT message.

        This is the most basic health check — if the simulator is
        running, it MUST be sending heartbeats at 1 Hz.

        CI Relevance:
          If this fails → SITL didn't start → container is broken.
        """
        msg = mavlink_connection.wait_heartbeat(timeout=HEARTBEAT_TIMEOUT)
        assert msg is not None, (
            f"No HEARTBEAT received within {HEARTBEAT_TIMEOUT}s. "
            f"SITL may not be running."
        )
        print(f"  ✅ Heartbeat confirmed (system_id={msg.get_srcSystem()})")

    def test_vehicle_type_is_quadrotor(self, mavlink_connection):
        """
        TEST 2: Verify the vehicle type is MAV_TYPE_QUADROTOR (type=2).

        We configured SITL to run ArduCopter, so the vehicle MUST
        identify as a quadrotor. This confirms the right firmware
        was loaded.

        CI Relevance:
          If this fails → wrong SITL vehicle type → Dockerfile config error.
        """
        msg = mavlink_connection.wait_heartbeat(timeout=HEARTBEAT_TIMEOUT)
        assert msg is not None, "No heartbeat to check vehicle type"

        MAV_TYPE_QUADROTOR = 2
        assert msg.type == MAV_TYPE_QUADROTOR, (
            f"Expected MAV_TYPE_QUADROTOR (type=2), "
            f"but got type={msg.type}. "
            f"Check that SITL is running ArduCopter, not ArduPlane/ArduRover."
        )
        print(f"  ✅ Vehicle type confirmed: QUADROTOR (type={msg.type})")

    def test_autopilot_is_ardupilot(self, mavlink_connection):
        """
        TEST 3: Verify the autopilot firmware is ArduPilot (autopilot=3).

        This confirms we're talking to an ArduPilot instance,
        not some other MAVLink-compatible system.

        CI Relevance:
          If this fails → something unexpected is on port 5760.
        """
        msg = mavlink_connection.wait_heartbeat(timeout=HEARTBEAT_TIMEOUT)
        assert msg is not None, "No heartbeat to check autopilot type"

        MAV_AUTOPILOT_ARDUPILOTMEGA = 3
        assert msg.autopilot == MAV_AUTOPILOT_ARDUPILOTMEGA, (
            f"Expected MAV_AUTOPILOT_ARDUPILOTMEGA (autopilot=3), "
            f"but got autopilot={msg.autopilot}."
        )
        print(f"  ✅ Autopilot confirmed: ArduPilotMega (autopilot={msg.autopilot})")


class TestSITLStatus:
    """Test suite: Verify SITL is in a sane state."""

    def test_system_status(self, mavlink_connection):
        """
        TEST 4: Verify system status is STANDBY or ACTIVE.

        After boot, SITL should be in STANDBY (ready to arm) or
        ACTIVE (already flying). Any other status indicates a problem.

        CI Relevance:
          If this fails → SITL booted but is in an error state.
        """
        msg = mavlink_connection.wait_heartbeat(timeout=HEARTBEAT_TIMEOUT)
        assert msg is not None, "No heartbeat to check system status"

        # MAV_STATE_STANDBY=3, MAV_STATE_ACTIVE=4, MAV_STATE_CALIBRATING=2
        valid_states = [2, 3, 4]
        assert msg.system_status in valid_states, (
            f"Unexpected system status: {msg.system_status}. "
            f"Expected one of {valid_states} (CALIBRATING/STANDBY/ACTIVE)."
        )
        state_names = {2: "CALIBRATING", 3: "STANDBY", 4: "ACTIVE"}
        print(f"  ✅ System status: {state_names.get(msg.system_status, 'UNKNOWN')}")
