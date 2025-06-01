import threading
import time
import RPi.GPIO as GPIO
import hardware_config as hc
from gate_controller import GateController
from led_manager import LEDManager

def run_gate_monitor(gate_controller_instance):
    gate_controller_instance.monitor()

def run_led_control(led_manager_instance):
    led_manager_instance.control_leds()

if __name__ == "__main__":
    # Initialize GPIO (once, globally)
    GPIO.setmode(GPIO.BOARD) # Or GPIO.BCM, depending on your pin numbering
    GPIO.setwarnings(False) # Optional: disable warnings

    gate_controllers = []
    # led_managers = [] # Though we only have one in this example

    try:
        gate1_controller = GateController(sensor_name="入口", 
                                        trig_pin=hc.GATE1_TRIG_PIN, 
                                        echo_pin=hc.GATE1_ECHO_PIN, 
                                        motor_pin=hc.GATE1_MOTOR_PIN, 
                                        api_url=hc.GATE1_API_URL, 
                                        threshold_cm=10)
        
        gate2_controller = GateController(sensor_name="出口", 
                                        trig_pin=hc.GATE2_TRIG_PIN, 
                                        echo_pin=hc.GATE2_ECHO_PIN, 
                                        motor_pin=hc.GATE2_MOTOR_PIN, 
                                        api_url=hc.GATE2_API_URL,
                                        threshold_cm=10)
        
        gate_controllers.extend([gate1_controller, gate2_controller])

        # led_main_manager = LEDManager(hc.LED_PINS)
        # led_managers.append(led_main_manager)

        gate1_thread = threading.Thread(target=run_gate_monitor, args=(gate1_controller,), daemon=True)
        gate2_thread = threading.Thread(target=run_gate_monitor, args=(gate2_controller,), daemon=True)
        # led_thread = threading.Thread(target=run_led_control, args=(led_main_manager,), daemon=True)

        gate1_thread.start()
        gate2_thread.start()
        # led_thread.start()

        print("🚀 系統啟動完成，按 Ctrl+C 可中止所有任務")
        while True:
            # Check if any thread has died, for more robust error handling if needed
            if not gate1_thread.is_alive() or not gate2_thread.is_alive() or not led_thread.is_alive():
                print("⚠️ 注意：有一個或多個執行緒已停止運作。")
                # Optionally, attempt to restart threads or perform other recovery actions here
                break # Exit main loop if a critical thread dies
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🔚 偵測到使用者中斷，準備清理資源...")
    finally:
        print("🚦 正在停止閘門監測...")
        for gc in gate_controllers:
            gc.stop_monitoring()

        # print("💡 正在停止LED控制器...")
        # for lm in led_managers: # Corrected variable name here
            # lm.stop_monitoring()
        
        # Wait for threads to finish their cleanup if they have long-running cleanup tasks
        # This might be overly cautious if stop_monitoring is quick
        if 'gate1_thread' in locals() and gate1_thread.is_alive(): gate1_thread.join(timeout=5)
        if 'gate2_thread' in locals() and gate2_thread.is_alive(): gate2_thread.join(timeout=5)
        # if 'led_thread' in locals() and led_thread.is_alive(): led_thread.join(timeout=5)

        GPIO.cleanup()
        print("✅ 所有 GPIO 腳位已清理完成，安全結束")
