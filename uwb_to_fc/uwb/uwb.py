from uwb.decawave_1001_uart import Decawave1001Driver
import time

class UWB:
    def __init__(self, port="/dev/ttyACM0", verbose=True):
        self.driver = Decawave1001Driver(port)
        self.verbose = verbose

        # smoothing factor (0.0–1.0)
        self.alpha = 1        # previous filtered position
        self.last_position = None

        self.get_version()
        self.get_config()

    def get_version(self):
        version = self.driver.get_ver()
        if self.verbose:
            print('Version: firmware {}, config {}, hardware {}'.format(
                version.get_firmware_version(),
                version.get_configuration_version(),
                version.get_hardware_version()
            ))

    def get_config(self):
        config = self.driver.get_cfg()
        if self.verbose:
            print('Tag: {}. Low Power {}. Loc Engine {}. LED {}. BLE {}. Firmware update {}'.format(
                config.tag,
                config.low_power_enabled,
                config.location_engine_enabled,
                config.led_enabled,
                config.ble_enabled,
                config.firmware_update_enabled
            ))

    def smooth_position(self, pos):
        """Exponential moving average filter"""

        if self.last_position is None:
            self.last_position = pos
            return pos

        filtered = {
            'x': self.alpha * pos['x'] + (1 - self.alpha) * self.last_position['x'],
            'y': self.alpha * pos['y'] + (1 - self.alpha) * self.last_position['y'],
            'z': self.alpha * pos['z'] + (1 - self.alpha) * self.last_position['z'],
            'quality': pos['quality']
        }

        self.last_position = filtered
        return filtered

    def get_location(self):
        try:
            response = self.driver.get_loc()  # get_loc() trả về vị trí + anchor data

            if response:
                tag_pos = response.get_tag_position()
                co_ords = tag_pos.position()
                quality_factor = tag_pos.quality_factor()

                pos = {
                    'x': co_ords[0] / 1000.0,
                    'y': co_ords[1] / 1000.0,
                    'z': co_ords[2] / 1000.0,
                    'quality': quality_factor
                }

                # Apply smoothing filter
                pos = self.smooth_position(pos)

                if self.verbose:
                    print(
                        "Filtered Position: x={:.3f}, y={:.3f}, z={:.3f}, quality={}".format(
                            pos['x'], pos['y'], pos['z'], pos['quality']
                        )
                    )

                return pos

            else:
                print("No response received for location request.")
                return None

        except Exception as e:
            print("Error occurred while fetching location:", e)
            return None


if __name__ == "__main__":
    uwb = UWB(port="/dev/ttyACM0")

    try:
        while True:
            uwb.get_location()
            time.sleep(1/10)  # 10 Hz
    except KeyboardInterrupt:
        print("Shutting down UWB.")