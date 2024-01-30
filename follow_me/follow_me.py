from __future__ import print_function

from dronekit import connect, VehicleMode, LocationGlobalRelative
import gps
import socket
import time
import sys

# Set up option parsing to get connection string
import argparse
parser = argparse.ArgumentParser(description='Tracks GPS position of your computer (Linux only).')
parser.add_argument('--connect',
                    help="Vehicle connection target string. If not specified, SITL automatically started and used.")
args = parser.parse_args()

# Connect to the Vehicle
connection_string = args.connect
sitl = None

# Start SITL if no connection string specified
print('Connecting to vehicle on: %s' % connection_string)
vehicle = connect(connection_string, wait_ready=True, timeout=300)

def arm_and_takeoff(aTargetAltitude):
    """
    Arms vehicle and fly to aTargetAltitude.
    """
    print("Basic pre-arm checks")
    # Dont try to arm until autopilot is ready
    while not vehicle.is_armable:
        print(" Waiting for vehicle to initialise...")
        time.sleep(1)

    print("Taking off!")
    vehicle.simple_takeoff(aTargetAltitude)  # Take off to target altitude

    # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command
    #  after Vehicle.simple_takeoff will execute immediately).
    while True:
        print(" Altitude: ", vehicle.location.global_relative_frame.alt)
        if vehicle.location.global_relative_frame.alt >= aTargetAltitude * 0.95: # Trigger just below target alt.
            print("Reached target altitude")
            break
        time.sleep(1)
    
try:
    # use the python gps package to access the laptop's gps
    gpsd = gps.gps(mode=gps.WATCH_ENABLE)

    # Arm and take of to altitude of 5 meters
    arm_and_takeoff(5)

    while True:
        if vehicle.mode.name != "GUIDED":
            print("User has changed flight modes - aborting follow-me")
            break

        # Get the current location of the laptop
        next(gpsd)

        # Once we have a valid location (see gpsd documentation) we can start moving our vehicle around
        if (gpsd.valid & gps.LATLON_SET) != 0:
            altitude = 30
            dest = LocationGlobalRelative(gpsd.fix.latitude, gpsd.fix.longitude, altitude)
            vehicle.simple_goto(dest)

            time.sleep(2)

except socket.error:
    print("Error: gpsd service does not seem to be running, plug in USB GPS or run run-fake-gps.sh")
    sys.exit(1)

print("Completed")
vehicle.close()

# Shut down simulator if it was started.
if sitl is not None:
    sitl.stop()

print("Completed")