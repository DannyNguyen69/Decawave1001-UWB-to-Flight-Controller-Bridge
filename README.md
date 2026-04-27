# UWB to Flight Controller Bridge

Dự án này kết nối module UWB **Decawave DWM1001** với flight controller (Pixhawk/ArduPilot) thông qua giao thức MAVLink. Vị trí từ UWB được gửi liên tục dưới dạng thông điệp `VISION_POSITION_ESTIMATE`, giúp EKF indoor hoạt động mà không cần GPS.

---

## 🗂️ Cấu trúc dự án

```
uwb_to_fc/
├── uwb_test.py                        # Entry point chính
├── uwb/
│   ├── __init__.py
│   ├── uwb.py                         # Class UWB – đọc và lọc vị trí
│   └── decawave_1001_uart/
│       ├── __init__.py
│       ├── decawave_1001.py           # UART driver cho DWM1001
│       └── messages/                  # Các message TLV của DWM1001
│           ├── dwm_config_response.py
│           ├── dwm_location_response.py
│           ├── dwm_position.py
│           ├── dwm_request.py
│           ├── dwm_response.py
│           ├── dwm_version_response.py
│           └── ...
└── drone/
    ├── __init__.py
    └── drone.py                       # Class Drone – kết nối FC qua DroneKit
```

---

## ⚙️ Yêu cầu hệ thống

- Python 3.7+
- Raspberry Pi (hoặc Linux board) với 2 cổng serial:
  - `/dev/ttyAMA0` → Flight Controller (Pixhawk)
  - `/dev/ttyACM0` → Module UWB DWM1001 (USB)

---

## 📦 Cài đặt thư viện

```bash
pip install -r requirements.txt
```

Hoặc cài thủ công:

```bash
pip install dronekit pyserial bitstring
```

---

## 🚀 Chạy chương trình

```bash
python3 uwb_test.py
```

Mặc định:
- Flight Controller: `/dev/ttyAMA0` (115200 baud)
- UWB module: `/dev/ttyACM0`
- Tần số gửi VPE: **10 Hz**

---

## 🔧 Cấu hình

Chỉnh trực tiếp trong `uwb_test.py`:

```python
RATE_HZ  = 10.0               # Tần số gửi (Hz)
port_fc  = "/dev/ttyAMA0"     # Cổng serial FC
port_uwb = "/dev/ttyACM0"     # Cổng USB UWB

# Tọa độ EKF origin – set về vị trí lab/thực địa của bạn
lat = int(10.762622 * 1e7)
lon = int(106.660172 * 1e7)
```

---

## 🧠 Cơ chế hoạt động

```
DWM1001 (UART) → uwb.py (get_location) → drone.py (send_uwb_location)
                                                    ↓
                               VISION_POSITION_ESTIMATE (MAVLink)
                                                    ↓
                                          Pixhawk EKF (indoor)
```

**Chuyển đổi tọa độ ENU → NED** (trong `drone.py`):
```
x_ned =  y_uwb
y_ned =  x_uwb
z_ned = -z_uwb
```

### Quy trình khởi động

1. Set EKF GPS Origin + Home Position (indoor mode, không cần GPS)
2. Warm-up 3 giây – gửi VPE liên tục để EKF hội tụ
3. Vào vòng lặp chính @ 10 Hz với **precise timing** (bù trừ thời gian xử lý)

---

## 📡 Hardware

| Thiết bị | Cổng | Ghi chú |
|---|---|---|
| Pixhawk / ArduPilot FC | `/dev/ttyAMA0` | UART, 115200 baud |
| Decawave DWM1001 Tag | `/dev/ttyACM0` | USB-UART |

---

## 📝 License

MIT License
