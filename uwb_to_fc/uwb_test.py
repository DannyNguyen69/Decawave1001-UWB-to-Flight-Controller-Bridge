import time

from uwb.uwb import UWB
from drone.drone import Drone

RATE_HZ = 10.0          # Tần số gửi 
INTERVAL = 1.0 / RATE_HZ


class UWBToFC:
    def __init__(self, verbose=True, port_fc="/dev/ttyAMA0", port_uwb="/dev/ttyACM0"):
        self.verbose = verbose
        self.uwb = UWB(port=port_uwb, verbose=False)
        self.drone = Drone(port=port_fc, verbose=verbose)
        self._home_set = False   # chỉ set home 1 lần duy nhất

    def set_home_to_current(self):
        """
        Set EKF origin + home position — đúng cách cho indoor/UWB không có GPS.
        Gọi TRƯỚC vòng lặp để FC có điểm gốc tọa độ ngay từ đầu.
        """
        lat = int(10.762622 * 1e7)   # latitude  (deg × 1e7) — tọa độ lab
        lon = int(106.660172 * 1e7)  # longitude (deg × 1e7)
        alt = int(0.0 * 1e3)         # altitude  (mm)
        mav    = self.drone.vehicle._master.mav
        sys_id = self.drone.vehicle._master.target_system

        print("[uwb_test] Setting EKF GPS origin (no-GPS indoor mode)...")
        mav.set_gps_global_origin_send(sys_id, lat, lon, alt, int(time.time() * 1e6))
        time.sleep(0.1)

        # Gửi thêm SET_HOME_POSITION để EKF có đủ tham chiếu altitude
        print("[uwb_test] Setting home position...")
        mav.set_home_position_send(
            sys_id,
            lat, lon, alt,         # lat, lon, alt
            0, 0, 0,               # x, y, z (local)
            [1, 0, 0, 0, 0, 0, 0, 0, 0],  # q (quaternion identity)
            0, 0, 0,               # approach x, y, z
            int(time.time() * 1e6),
        )
        time.sleep(0.4)
        print("[uwb_test] EKF origin + home set.")

    def run(self):
        # ── Set EKF origin TRƯỚC vòng lặp, không chờ UWB data ───────────
        self.set_home_to_current()
        self._home_set = True

        # ── Warm-up: gửi VPE liên tục 3 giây để EKF hội tụ trước khi arm ─
        print("[uwb_test] Warming up EKF (3s)...")
        warmup_end = time.time() + 3.0
        while time.time() < warmup_end:
            data = self.uwb.get_location()
            if data is not None:
                self.drone.send_uwb_location(data)
            time.sleep(INTERVAL)
        print("[uwb_test] EKF warm-up done. Starting main loop @ {} Hz...".format(RATE_HZ))
        # ──────────────────────────────────────────────────────────────────

        sent = 0
        missed = 0

        try:
            while True:
                t0 = time.time()   # ← ghi nhận đầu chu kỳ

                data = self.uwb.get_location()

                if data is not None:
                    self.drone.send_uwb_location(data)
                    sent += 1

                    if self.verbose:
                        print("[uwb_test] [{:>5}] Sent: x={:.3f}, y={:.3f}, z={:.3f}, quality={}".format(
                            sent, data['x'], data['y'], data['z'], data['quality']
                        ))
                else:
                    missed += 1
                    print("[uwb_test] [WARN] Không đọc được UWB (missed={})".format(missed))

                # Precise timing: bù trừ thời gian xử lý
                elapsed = time.time() - t0
                sleep_t = INTERVAL - elapsed
                if sleep_t > 0:
                    time.sleep(sleep_t)

        except KeyboardInterrupt:
            print("\n[uwb_test] Dừng. Đã gửi {} frame, bỏ lỡ {} frame.".format(sent, missed))
            self.drone.shutdown()


if __name__ == "__main__":
    verbose = True
    port_fc  = "/dev/ttyAMA0"
    port_uwb = "/dev/ttyACM0"
    node = UWBToFC(verbose=verbose, port_fc=port_fc, port_uwb=port_uwb)
    node.run()

