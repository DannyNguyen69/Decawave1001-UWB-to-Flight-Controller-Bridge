# UWB to Flight Controller Bridge

This project bridges a **Decawave DWM1001** Ultra-Wideband module with a MAVLink-based flight controller (Pixhawk / ArduPilot). UWB position data is continuously sent as `VISION_POSITION_ESTIMATE` messages, enabling indoor EKF-based localization without GPS.

---

## Project Structure

```
uwb_to_fc/
├── uwb_test.py                        # Main entry point
├── uwb/
│   ├── __init__.py
│   ├── uwb.py                         # UWB class – reads and filters position
│   └── decawave_1001_uart/
│       ├── __init__.py
│       ├── decawave_1001.py           # UART driver for DWM1001
│       └── messages/                  # TLV message definitions
│           ├── dwm_config_response.py
│           ├── dwm_location_response.py
│           ├── dwm_position.py
│           ├── dwm_request.py
│           ├── dwm_response.py
│           ├── dwm_version_response.py
│           └── ...
└── drone/
    ├── __init__.py
    └── drone.py                       # Drone class – connects FC via DroneKit
```

---

## System Requirements

- Python 3.7+
- Raspberry Pi or any Linux-based board with two serial ports:
  - `/dev/ttyAMA0` — Flight Controller (Pixhawk)
  - `/dev/ttyACM0` — DWM1001 UWB Tag (USB)

---

## Installation

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install dronekit pyserial bitstring
```

---

## Usage

```bash
python3 uwb_test.py
```

Defaults:
- Flight Controller: `/dev/ttyAMA0` at 115200 baud
- UWB module: `/dev/ttyACM0`
- Send rate: **10 Hz**

---

## Configuration

Edit the top of `uwb_test.py`:

```python
RATE_HZ  = 10.0               # Send rate in Hz
port_fc  = "/dev/ttyAMA0"     # Flight controller serial port
port_uwb = "/dev/ttyACM0"     # UWB module USB port

# EKF origin coordinates – set to your actual field location
lat = int(10.762622 * 1e7)
lon = int(106.660172 * 1e7)
```

---

## How It Works

```
DWM1001 (UART) -> uwb.py (get_location) -> drone.py (send_uwb_location)
                                                    |
                               VISION_POSITION_ESTIMATE (MAVLink)
                                                    |
                                          Pixhawk EKF (indoor)
```

**Coordinate conversion ENU (UWB) to NED (Pixhawk)** in `drone.py`:
```
x_ned =  y_uwb
y_ned =  x_uwb
z_ned = -z_uwb
```

### Startup Sequence

1. Set EKF GPS Origin and Home Position (indoor mode, no GPS required)
2. 3-second warm-up — continuously sends VPE to let EKF converge before arming
3. Main loop at 10 Hz with **precise timing** (compensates for processing overhead)

---

## Hardware

| Device | Port | Notes |
|---|---|---|
| Pixhawk / ArduPilot FC | `/dev/ttyAMA0` | UART, 115200 baud |
| Decawave DWM1001 Tag | `/dev/ttyACM0` | USB-UART |

---

## License

MIT License
