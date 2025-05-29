import RPi.GPIO as GPIO
import time

class LEDController:
    def __init__(self, pin, color_name="red", frequency=100):
        self.pin = pin
        self.color = color_name
        self.frequency = frequency

        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin, GPIO.OUT)

        self.pwm = GPIO.PWM(self.pin, self.frequency)
        self.pwm.start(0)
        print(f"[INIT] {self.color} LED 初始化完成 (GPIO{self.pin})")

    def set_brightness(self, duty):
        """設定亮度：0～100"""
        if 0 <= duty <= 100:
            self.pwm.ChangeDutyCycle(duty)
            print(f"[PWM] {self.color} LED 亮度: {duty}%")
        else:
            print(f"⚠️ Duty Cycle 值不合法: {duty}")

    def stop(self):
        """停止 PWM 並清理 GPIO"""
        self.pwm.stop()
        GPIO.cleanup(self.pin)
        print(f"[CLEANUP] {self.color} LED 停止並清理資源")


class MultiLEDController:
    def __init__(self, led_pins, exclude=[]):
        self.leds = {}
        for color, pin in led_pins.items():
            if color not in exclude:
                self.leds[color] = LEDController(pin, color_name=color)
                self.leds[color].set_brightness(100)
            else:
                print(f"[SKIP] {color} LED 被排除")

    def turn_off_all(self):
        for led in self.leds.values():
            led.set_brightness(0)

    def stop_all(self):
        for led in self.leds.values():
            led.stop()


# ========== 單顆 LED 測試 ==========
# if __name__ == "__main__":
#     red_led = LEDController(pin=35, color_name="green")

#     try:
#         while True:
#             red_led.set_brightness(100)
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("🔚 使用者中斷程式")
#     finally:
#         red_led.stop()
