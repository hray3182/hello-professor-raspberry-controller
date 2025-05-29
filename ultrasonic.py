# ultrasonic_module.py
import time
import RPi.GPIO as GPIO

class UltrasonicController:
    def __init__(self, trig_pin, echo_pin, threshold_cm=30):
        self.trig_pin = trig_pin
        self.echo_pin = echo_pin
        self.threshold_cm = threshold_cm
        self.car_detected = False

        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(self.trig_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)
        GPIO.output(self.trig_pin, False)
        time.sleep(0.5)  # 初始化穩定時間

    def measure_distance(self):
        # 發出超聲波脈衝
        GPIO.output(self.trig_pin, True)
        time.sleep(0.00001)
        GPIO.output(self.trig_pin, False)

        # 等待回音開始
        start_time = time.time()
        timeout = start_time + 0.04
        while GPIO.input(self.echo_pin) == 0 and time.time() < timeout:
            start_time = time.time()

        # 等待回音結束
        end_time = time.time()
        timeout = end_time + 0.04
        while GPIO.input(self.echo_pin) == 1 and time.time() < timeout:
            end_time = time.time()

        # 計算距離（cm）
        elapsed = end_time - start_time
        distance = (elapsed * 34300) / 2
        return distance

    def check_for_car(self):
        distance = self.measure_distance()
        print(f"[INFO] 距離: {distance:.2f} cm")
        if distance < self.threshold_cm:
            if not self.car_detected:
                print("[DETECTED] 車輛進入範圍")
            self.car_detected = True
        else:
            if self.car_detected:
                print("[CLEARED] 車輛離開範圍")
            self.car_detected = False

        return self.car_detected

    def cleanup(self):
        GPIO.cleanup()

# 測試程式區塊（只有在直接執行這個檔案時才會跑）
if __name__ == "__main__":
    try:
        sensor = UltrasonicController(trig_pin=36, echo_pin=38)
        while True:
            car = sensor.check_for_car()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[EXIT] 手動中止")
    finally:
        sensor.cleanup()
