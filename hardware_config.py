# hardware_config.py

# Gate Controller Pins
GATE1_TRIG_PIN = 35
GATE1_ECHO_PIN = 37
GATE1_MOTOR_PIN = 40

GATE2_TRIG_PIN = 36
GATE2_ECHO_PIN = 38
GATE2_MOTOR_PIN = 32

# LED Pins Configuration
LED_PINS = {
    "red1": 3, "red2": 5, "red3": 7,
    "red4": 11, "red5": 15, "red6": 19
}

# API Configuration
# LICENSE_PLATE_API_URL = "https://dev8000.hraydev.xyz/capture" # 舊的可以移除或註解

GATE1_API_URL = "https://dev8000.hraydev.xyz/entry/capture"
GATE2_API_URL = "https://dev8000.hraydev.xyz/exit/capture"

# API for Parking Records
PARKING_RECORD_ENTRY_API_URL = "http://localhost:8080/api/v1/parking-records/entry" # 雖然目前未使用，但保留定義
PARKING_RECORD_EXIT_API_URL = "https://api-hello-professor.zeabur.app/api/v1/parking-records/exit" # 新增出口記錄 API