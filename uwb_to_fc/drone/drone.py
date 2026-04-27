from __future__ import print_function
from dronekit import connect, VehicleMode
import time


class Control:
    """Dieu khien arm/takeoff dung DroneKit."""

    def __init__(self, vehicle, verbose=True):
        self.vehicle = vehicle
        self.verbose = verbose

    def arm(self, value=True):
        if value:
            print("[Control] Arming motors...")
            self.vehicle.armed = True
            while not self.vehicle.armed:
                time.sleep(0.1)
            print("[Control] Motors armed.")
        else:
            print("[Control] Disarming motors...")
            self.vehicle.armed = False

    def takeoff(self, altitude=1.0):
        print("[Control] Takeoff to {}m...".format(altitude))
        self.vehicle.simple_takeoff(altitude)


class Drone:
    """
    Ket noi FC qua DroneKit (flight control) va gui
    VISION_POSITION_ESTIMATE truc tiep trong vong lap chinh (khong co background thread).

    ENU (UWB) -> NED (Pixhawk):
        x_ned =  y_uwb
        y_ned =  x_uwb
        z_ned = -z_uwb

    QUAN TRONG: send_uwb_location() phai duoc goi trong vong lap chinh voi dung tan so
    (KHONG dung background thread) de FC nhan dung nhip.
    """

    def __init__(self, port="/dev/ttyACM0", baud=115200, verbose=True):
        self.verbose = verbose

        print("[Drone] Dang ket noi FC tai {} ({} baud)...".format(port, baud))
        self.vehicle = connect(port, baud, wait_ready=True)
        self.vehicle.wait_ready('autopilot_version')
        self.control = Control(self.vehicle, verbose=verbose)

        if self.verbose:
            print("[Drone] Ket noi thanh cong! Firmware: {}".format(self.vehicle.version))

    # ─────────── Mode ───────────

    def get_mode(self):
        """Tra ve ten mode hien tai (string), vi du 'GUIDED', 'LOITER'."""
        return self.vehicle.mode.name

    # ─────────── VISION_POSITION_ESTIMATE ───────────

    def send_uwb_location(self, location):
        """
        Gui VISION_POSITION_ESTIMATE len Pixhawk.
        Goi truc tiep trong vong lap chinh (khong dung background thread)
        de dam bao FC nhan dung tan so.

        Args:
            location: dict voi keys x, y, z (don vi met, he ENU)
        """
        if location is None:
            return

        # ENU (UWB) -> NED (Pixhawk)
        x_ned =  location['y']
        y_ned =  location['x']
        z_ned = -location['z']

        try:
            self.vehicle._master.mav.vision_position_estimate_send(
                int(time.time() * 1e6),  # usec timestamp
                x_ned,                   # X NED (m)
                y_ned,                   # Y NED (m)
                z_ned,                   # Z NED (m) -- KHONG dung NaN
                0, 0, 0,  # roll, pitch, yaw
            )
        except Exception as e:
            print("[Drone] Loi gui VPE:", e)

        if self.verbose:
            print("[Drone] VPE: x={:.3f} y={:.3f} z={:.3f}".format(
                location['x'], location['y'], location['z']))

    # ─────────── Helpers ───────────

    def get_master(self):
        """Tra ve mavlink master de dung chung (vi du set EKF origin)."""
        return self.vehicle._master

    def shutdown(self):
        self.vehicle.close()
        print("[Drone] Da dong ket noi FC.")
