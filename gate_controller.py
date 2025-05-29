import time
import RPi.GPIO as GPIO
import requests
from moto import MotorController
from ultrasonic import UltrasonicController

class GateController:
    def __init__(self, sensor_name, trig_pin, echo_pin, motor_pin, api_url, threshold_cm=30, open_angle=180, close_angle=90):
        self.sensor_name = sensor_name
        self.api_url = api_url
        # It's good practice to ensure GPIO mode is set before using pins.
        # However, if other modules also set it, this might cause warnings if not coordinated.
        # For now, assuming it's handled globally or in each component.
        self.sensor = UltrasonicController(trig_pin, echo_pin, threshold_cm=threshold_cm)
        self.motor = MotorController(motor_pin)
        self.has_opened = False
        self.leave_count = 0
        self.enter_count = 0
        self.running = True

    def monitor(self):
        print(f"[{self.sensor_name}] 啟動監測中...")
        try:
            while self.running:
                car_detected = self.sensor.check_for_car()

                if car_detected:
                    self.leave_count = 0
                    if not self.has_opened:
                        print(f"[{self.sensor_name}] 偵測到車輛，準備呼叫車牌辨識 API...")
                        try:
                            response = requests.get(self.api_url, timeout=5)
                            response.raise_for_status()
                            api_data = response.json()
                            print(f"[{self.sensor_name}] API 回應: {api_data}")

                            if api_data.get("ocr_format_valid") is True and "License plate detected" in api_data.get("message", ""):
                                print(f"[{self.sensor_name}] 車牌辨識成功且格式有效 ({api_data.get('ocr_text_cleaned')}) → 開啟柵欄")
                                self.motor.open_gate()
                                self.has_opened = True
                                self.enter_count = 0
                            else:
                                print(f"[{self.sensor_name}] 車牌辨識失敗或格式無效。API原始訊息: {api_data.get('message')}")

                        except requests.exceptions.RequestException as e:
                            print(f"[{self.sensor_name}] 呼叫 API 時發生錯誤: {e}")
                        except ValueError:
                            print(f"[{self.sensor_name}] 解析 API 回應失敗 (非 JSON 格式)")
                else:
                    if self.has_opened:
                        self.leave_count += 1
                        print(f"[{self.sensor_name}] 車輛可能離開，離開偵測計數：{self.leave_count}")
                        if self.leave_count >= 2:
                            print(f"[{self.sensor_name}] 確認車輛已離開 → 關閉柵欄")
                            self.motor.close_gate()
                            self.has_opened = False
                            self.leave_count = 0
                            self.enter_count = 0
                time.sleep(1)
        except Exception as e:
            print(f"[{self.sensor_name}]監測時發生錯誤: {e}")
        finally:
            # This cleanup is now part of stop_monitoring
            # to be called explicitly when the thread is asked to stop.
            pass


    def stop_monitoring(self):
        self.running = False
        print(f"[{self.sensor_name}] 停止監測")
        # Ensure motor and sensor resources are cleaned up.
        # These methods should exist in your MotorController and UltrasonicController
        if hasattr(self.motor, 'destroy'):
            self.motor.destroy()
        if hasattr(self.sensor, 'cleanup'):
            self.sensor.cleanup() 