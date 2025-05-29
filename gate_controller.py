import time
import RPi.GPIO as GPIO
from moto import MotorController
from ultrasonic import UltrasonicController

class GateController:
    def __init__(self, sensor_name, trig_pin, echo_pin, motor_pin, threshold_cm=30):
        self.sensor_name = sensor_name
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
                        self.enter_count += 1
                        if self.enter_count >= 2:
                            print(f"[{self.sensor_name}] 進入次數：{self.enter_count}")
                            print(f"[{self.sensor_name}] 偵測到車輛 → 開啟柵欄")
                            print('輸出API到手機頁面要求拍照')
                            self.motor.open_gate()
                            self.has_opened = True
                else:
                    self.enter_count = 0
                    if self.has_opened:
                        self.leave_count += 1
                        print(f"[{self.sensor_name}] 離開次數：{self.leave_count}")
                        if self.leave_count >= 2:
                            print(f"[{self.sensor_name}] 車輛離開確認 → 關閉柵欄")
                            self.motor.close_gate()
                            self.has_opened = False
                            self.leave_count = 0
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