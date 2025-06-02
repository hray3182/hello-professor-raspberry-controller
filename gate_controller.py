import time
import RPi.GPIO as GPIO
import requests
from moto import MotorController
from ultrasonic import UltrasonicController

class GateController:
    def __init__(self, sensor_name, trig_pin, echo_pin, motor_pin, api_url, threshold_cm=30, open_angle=180, close_angle=90, parking_record_api_url=None, parking_exit_record_api_url=None):
        self.sensor_name = sensor_name
        self.api_url = api_url
        self.parking_record_api_url = parking_record_api_url
        self.parking_exit_record_api_url = parking_exit_record_api_url
        self.sensor = UltrasonicController(trig_pin, echo_pin, threshold_cm=threshold_cm)
        self.motor = MotorController(motor_pin, open_angle=open_angle, close_angle=close_angle)
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

                            if api_data.get("ocr_format_valid") is True:
                                license_plate_text = api_data.get('ocr_text_cleaned', 'N/A')
                                
                                if self.sensor_name == "出口" and self.parking_exit_record_api_url:
                                    print(f"[{self.sensor_name}] 車牌格式有效 ({license_plate_text})，準備呼叫出口記錄 API...")
                                    exit_payload = {"licensePlate": license_plate_text}
                                    try:
                                        exit_response = requests.post(self.parking_exit_record_api_url, json=exit_payload, timeout=5)
                                        print(f"[{self.sensor_name}] 出口記錄 API 回應狀態碼: {exit_response.status_code}")
                                        if exit_response.status_code == 200:
                                            print(f"[{self.sensor_name}] 出口記錄 API 成功 (200) → 開啟柵欄")
                                            self.motor.open_gate()
                                            self.has_opened = True
                                            self.enter_count = 0
                                        else:
                                            print(f"[{self.sensor_name}] 出口記錄 API 失敗 (狀態碼: {exit_response.status_code})，柵欄不開啟。回應: {exit_response.text}")
                                    except requests.exceptions.RequestException as exit_e:
                                        print(f"[{self.sensor_name}] 呼叫出口記錄 API 時發生錯誤: {exit_e}，柵欄不開啟。")
                                
                                elif self.sensor_name != "出口" or not self.parking_exit_record_api_url:
                                    print(f"[{self.sensor_name}] 車牌格式有效 ({license_plate_text}) → 開啟柵欄 (非出口記錄流程或出口記錄API未設定)")
                                    self.motor.open_gate()
                                    self.has_opened = True
                                    self.enter_count = 0
                            else:
                                print(f"[{self.sensor_name}] 車牌格式無效或 API 未返回有效格式。API原始訊息: {api_data.get('message', '無法取得訊息')}")

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
            pass

    def stop_monitoring(self):
        self.running = False
        print(f"[{self.sensor_name}] 停止監測")
        if hasattr(self.motor, 'destroy'):
            self.motor.destroy()
        if hasattr(self.sensor, 'cleanup'):
            self.sensor.cleanup() 