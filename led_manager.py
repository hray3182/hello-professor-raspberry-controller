from LED import LEDController

class LEDManager:
    def __init__(self, led_pins):
        self.led_pins = led_pins
        self.leds = {}
        self.states = {}
        self.running = True

        # 初始化所有 LED 為亮起狀態
        for name, pin in self.led_pins.items():
            self.leds[name] = LEDController(pin, color_name=name)
            self.leds[name].set_brightness(100)
            self.states[name] = True  # True 表示亮

        print("💡 所有LED已亮起。輸入 1~6 控制 red1~red6 開/關（再次輸入可切換）")

    def control_leds(self):
        try:
            while self.running:
                user_input = input("輸入1~6切換燈狀態（Ctrl+C 結束）：>> ").strip()
                if user_input in {str(i) for i in range(1, len(self.led_pins) + 1)}:
                    led_key = f"red{user_input}"
                    if led_key in self.leds:
                        if self.states[led_key]:
                            self.leds[led_key].set_brightness(0)
                            print(f"🔴 {led_key} 已關閉")
                        else:
                            self.leds[led_key].set_brightness(100)
                            print(f"🟢 {led_key} 已打開")
                        self.states[led_key] = not self.states[led_key]
                else:
                    print(f"⚠️ 請輸入有效的數字（1~{len(self.led_pins)}）")
        except KeyboardInterrupt:
            # Handled by the main thread's KeyboardInterrupt
            pass
        except Exception as e:
            print(f"[LED Manager] 控制LED時發生錯誤: {e}")
        # Cleanup is handled by stop_monitoring

    def stop_monitoring(self):
        self.running = False
        print("\n[LED Manager] 停止LED監控")
        for led in self.leds.values():
            if hasattr(led, 'stop'): # Ensure stop method exists
                led.stop() 