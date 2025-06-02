import time
import RPi.GPIO as GPIO
import requests
from moto import MotorController
from ultrasonic import UltrasonicController

class GateController:
    def __init__(self, sensor_name, trig_pin, echo_pin, motor_pin, api_url, threshold_cm=30, open_angle=180, close_angle=90, parking_record_api_url=None, parking_exit_record_api_url=None, payment_status_api_base_url=None):
        self.sensor_name = sensor_name
        self.api_url = api_url
        self.parking_record_api_url = parking_record_api_url
        self.parking_exit_record_api_url = parking_exit_record_api_url
        self.payment_status_api_base_url = payment_status_api_base_url
        self.sensor = UltrasonicController(trig_pin, echo_pin, threshold_cm=threshold_cm)
        self.motor = MotorController(motor_pin, open_angle=open_angle, close_angle=close_angle)
        self.has_opened = False
        self.leave_count = 0
        self.enter_count = 0
        self.running = True
        self.last_recognized_plate = None

    def monitor(self):
        print(f"[{self.sensor_name}] 啟動監測中...")
        try:
            while self.running:
                car_detected = self.sensor.check_for_car()

                if car_detected:
                    self.leave_count = 0
                    if not self.has_opened:
                        print(f"[{self.sensor_name}] 偵測到車輛，準備呼叫車牌辨識 API ({self.api_url})...")
                        try:
                            response = requests.get(self.api_url, timeout=5)
                            response.raise_for_status()
                            api_data = response.json()
                            print(f"[{self.sensor_name}] 車牌辨識 API 回應: {api_data}")

                            if api_data.get("ocr_format_valid") is True:
                                self.last_recognized_plate = api_data.get('ocr_text_cleaned', 'N/A')
                                
                                if self.sensor_name == "出口" and self.payment_status_api_base_url:
                                    payment_check_url = f"{self.payment_status_api_base_url}{self.last_recognized_plate}"
                                    print(f"[{self.sensor_name}] 車牌格式有效 ({self.last_recognized_plate})，準備呼叫付款狀態檢查 API: {payment_check_url}")
                                    try:
                                        payment_response = requests.get(payment_check_url, timeout=5)
                                        payment_response.raise_for_status()
                                        payment_data = payment_response.json()
                                        print(f"[{self.sensor_name}] 付款狀態 API 回應: {payment_data}")
                                        
                                        if payment_data.get("payment_status") == "Paid":
                                            print(f"[{self.sensor_name}] 付款狀態為 'Paid' → 開啟柵欄")
                                            self.motor.open_gate()
                                            self.has_opened = True
                                            self.enter_count = 0
                                        else:
                                            print(f"[{self.sensor_name}] 付款狀態不為 'Paid' (狀態: {payment_data.get('payment_status')})，柵欄不開啟。")
                                    except requests.exceptions.RequestException as payment_e:
                                        print(f"[{self.sensor_name}] 呼叫付款狀態 API 時發生錯誤: {payment_e}，柵欄不開啟。")
                                    except ValueError:
                                        print(f"[{self.sensor_name}] 解析付款狀態 API 回應失敗 (非 JSON 格式)，柵欄不開啟。")
                                
                                elif self.sensor_name != "出口" or not self.payment_status_api_base_url:
                                    print(f"[{self.sensor_name}] 車牌格式有效 ({self.last_recognized_plate}) → 開啟柵欄 (非出口付款檢查流程)")
                                    self.motor.open_gate()
                                    self.has_opened = True
                                    self.enter_count = 0
                            else:
                                print(f"[{self.sensor_name}] 車牌格式無效或 API 未返回有效格式。API原始訊息: {api_data.get('message', '無法取得訊息')}")
                                self.last_recognized_plate = None

                        except requests.exceptions.RequestException as e:
                            print(f"[{self.sensor_name}] 呼叫車牌辨識 API 時發生錯誤: {e}")
                            self.last_recognized_plate = None
                        except ValueError:
                            print(f"[{self.sensor_name}] 解析車牌辨識 API 回應失敗 (非 JSON 格式)")
                            self.last_recognized_plate = None
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
                            
                            if self.sensor_name == "出口" and self.parking_exit_record_api_url and self.last_recognized_plate and self.last_recognized_plate != 'N/A':
                                print(f"[{self.sensor_name}] 閘門已關閉，準備為車牌 {self.last_recognized_plate} 呼叫出口記錄 API: {self.parking_exit_record_api_url}")
                                exit_payload = {"licensePlate": self.last_recognized_plate}
                                try:
                                    exit_response = requests.post(self.parking_exit_record_api_url, json=exit_payload, timeout=5)
                                    exit_response.raise_for_status()
                                    print(f"[{self.sensor_name}] 出口記錄 API 呼叫成功: {exit_response.status_code} - {exit_response.text}")
                                except requests.exceptions.RequestException as exit_e:
                                    print(f"[{self.sensor_name}] 呼叫出口記錄 API 時發生錯誤: {exit_e}")
                                finally:
                                    self.last_recognized_plate = None
                            elif self.last_recognized_plate:
                                self.last_recognized_plate = None
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