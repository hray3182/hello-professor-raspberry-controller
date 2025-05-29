import RPi.GPIO as GPIO
import time


class MotorController:
    def __init__(self, pin):
        self.pin = pin
        self.angle = 0
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin, 50)  # 50Hz frequency
        self.pwm.start(0)

    def destroy(self):
        self.pwm.stop()
        GPIO.cleanup()

# 輸入0 ～ 180度即可
# 別超過180度
    def setDirection(self):
        # 0 = 停止轉動
        # 2 = 0度
        # 7 = 90度
        # 12 = 180度
        duty = 2 + (self.angle / 18)
        self.pwm.ChangeDutyCycle(duty)
        # 消除抖動
        time.sleep(0.3)
        self.pwm.ChangeDutyCycle(0)
        print("角度=", self.angle, "-> duty=", duty)

    def reset(self):
        self.angle = 0
        self.setDirection()
    
    def open_gate(self):
        self.angle = 180 
        self.setDirection()
    
    def close_gate(self):
        self.angle = 90
        self.setDirection()

    def test(self):
        while True:
            self.angle = 0
            self.setDirection()
            time.sleep(0.5)
            self.angle = 180
            self.setDirection()
            time.sleep(0.5)


if __name__ == "__main__":
    try:
        motor = MotorController(40)
        # motor.reset()
        # motor.open_gate()
        # time.sleep(1)
        # motor.close_gate()
        motor.test()
    finally:
        print("清理 GPIO 資源")
        motor.destroy()
