import threading
import time
import RPi.GPIO as GPIO
from moto import MotorController
from ultrasonic import UltrasonicController
from LED import MultiLEDController, LEDController

def monitor_gate(sensor_name, trig_pin, echo_pin, motor_pin):
    sensor = UltrasonicController(trig_pin, echo_pin, threshold_cm=30)
    motor = MotorController(motor_pin)
    has_opened = False
    leave_count = 0
    enter_count = 0

    try:
        print(f"[{sensor_name}] 啟動監測中...")
        while True:
            car_detected = sensor.check_for_car()

            if car_detected:
                leave_count = 0
                if not has_opened:
                    enter_count += 1
                    if enter_count >= 2:
                        print(f"[{sensor_name}] 進入次數：{enter_count}")
                        print(f"[{sensor_name}] 偵測到車輛 → 開啟柵欄")
                        print('輸出API到手機頁面要求拍照')
                        motor.open_gate()
                        has_opened = True
            else:
                enter_count = 0
                if has_opened:
                    leave_count += 1
                    print(f"[{sensor_name}] 離開次數：{leave_count}")
                    if leave_count >= 2:
                        print(f"[{sensor_name}] 車輛離開確認 → 關閉柵欄")
                        motor.close_gate()
                        has_opened = False
                        leave_count = 0
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"[{sensor_name}] 停止監測")
    finally:
        motor.destroy()
        sensor.cleanup()


def monitor_leds():
    led_pins = {
        "red1": 3,
        "red2": 5,
        "red3": 7,
        "red4": 11,
        "red5": 15, # 13 腳壞了
        "red6": 19
    }
    
    # 初始化所有 LED 為亮起狀態
    leds = {}
    states = {}
    for name, pin in led_pins.items():
        leds[name] = LEDController(pin, color_name=name)
        leds[name].set_brightness(100)
        states[name] = True  # True 表示亮

    print("💡 所有LED已亮起。輸入 1~6 控制 red1~red6 開/關（再次輸入可切換）")

    try:
        while True:
            user_input = input("輸入1~6切換燈狀態（Ctrl+C 結束）：>> ").strip()
            if user_input in {"1", "2", "3", "4", "5", "6"}:
                led_key = f"red{user_input}"
                if led_key in leds:
                    if states[led_key]:
                        leds[led_key].set_brightness(0)
                        print(f"🔴 {led_key} 已關閉")
                    else:
                        leds[led_key].set_brightness(100)
                        print(f"🟢 {led_key} 已打開")
                    states[led_key] = not states[led_key]
            else:
                print("⚠️ 請輸入有效的數字（1~6）")
    except KeyboardInterrupt:
        print("\n[LED] 停止LED監控")
    finally:
        for led in leds.values():
            led.stop()


if __name__ == "__main__":
    try:
        gate1 = threading.Thread(target=monitor_gate, args=("入口", 35, 37, 40), daemon=True)
        gate2 = threading.Thread(target=monitor_gate, args=("出口", 36, 38, 32), daemon=True)
        led_thread = threading.Thread(target=monitor_leds, daemon=True)

        gate1.start()
        gate2.start()
        led_thread.start()

        print("🚀 系統啟動完成，按 Ctrl+C 可中止所有任務")
        while True:
            time.sleep(1)  # 保持主執行緒活著，等待中斷

    except KeyboardInterrupt:
        print("\n🔚 偵測到使用者中斷，準備清理資源...")
    finally:
        GPIO.cleanup()
        print("✅ 所有 GPIO 腳位已清理完成，安全結束")
