import evdev
from evdev import ecodes
import threading
import time
import os

class GlobalHotkeyListener:
    def __init__(self, callback_start, callback_stop, hotkey_mode=None):
        """
        callback_start: función al iniciar grabación
        callback_stop: función al detener grabación
        hotkey_mode: None (usa FERDONAN_HOTKEY_MODE env), "alt_c", "copilot_toggle"
        """
        self.callback_start = callback_start
        self.callback_stop = callback_stop
        
        # Determinar modo desde env o parámetro
        if hotkey_mode is None:
            hotkey_mode = os.environ.get("FERDONAN_HOTKEY_MODE", "alt_c")
        self.mode = hotkey_mode
        
        self.running = False
        self.thread = None
        self.alt_pressed = False
        self.recording = False
        self.copilot_state = False  # Para modo toggle
        
        # Buscar teclado
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        self.keyboard = None
        for dev in devices:
            if 'keyboard' in dev.name.lower() or 'kbd' in dev.name.lower():
                self.keyboard = dev
                print(f"[Hotkey] Usando teclado: {dev.name}")
                break
        
        if not self.keyboard:
            raise RuntimeError("No se encontró dispositivo de teclado")
        
        # Mostrar modo activo
        if self.mode == "alt_c":
            print("[Hotkey] Modo: ALT+C (mantén presionado para grabar, suelta para procesar)")
        elif self.mode == "copilot_toggle":
            print("[Hotkey] Modo: COPILOT (presiona para iniciar, vuelve a presionar para detener)")
        else:
            print(f"[Hotkey] Modo desconocido: {self.mode}, usando alt_c")
            self.mode = "alt_c"
    
    def start(self):
        """Inicia el listener en un hilo separado"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
        print("[Hotkey] Listener activo - esperando tecla...")
    
    def stop(self):
        """Detiene el listener"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
    
    def _listen(self):
        """Bucle principal de escucha de eventos"""
        try:
            for event in self.keyboard.read_loop():
                if not self.running:
                    break
                
                if event.type == ecodes.EV_KEY:
                    key_event = evdev.categorize(event)
                    
                    if self.mode == "alt_c":
                        # Modo Alt+C: mantener presionado
                        if key_event.keycode == 'KEY_LEFTALT':
                            self.alt_pressed = (key_event.keystate == key_event.key_down)
                        elif key_event.keycode == 'KEY_C':
                            if key_event.keystate == key_event.key_down and self.alt_pressed:
                                if not self.recording:
                                    self.recording = True
                                    print("[Hotkey] 🎤 Iniciando grabación (mantén presionado)...")
                                    self.callback_start()
                            elif key_event.keystate == key_event.key_up and self.recording:
                                self.recording = False
                                print("[Hotkey] ⏹️  Grabación finalizada, procesando...")
                                self.callback_stop()
                                time.sleep(0.1)
                    
                    elif self.mode == "copilot_toggle":
                        # Modo Copilot: toggle (presionar para iniciar/detener)
                        if key_event.keycode == 'KEY_F23' and key_event.keystate == key_event.key_down:
                            self.copilot_state = not self.copilot_state
                            if self.copilot_state:
                                print("[Hotkey] 🎤 Iniciando grabación (modo toggle)...")
                                self.callback_start()
                            else:
                                print("[Hotkey] ⏹️  Deteniendo grabación, procesando...")
                                self.callback_stop()
                            time.sleep(0.3)  # Evitar rebotes
        except Exception as e:
            print(f"[Hotkey] Error en listener: {e}")

# Prueba
if __name__ == "__main__":
    def on_start():
        print("🎙️ [SIM] Grabando audio...")
    
    def on_stop():
        print("🎙️ [SIM] Procesando comando de voz...")
    
    # Cambia la variable de entorno para probar diferentes modos
    # os.environ["FERDONAN_HOTKEY_MODE"] = "copilot_toggle"  # Descomenta para probar Copilot
    
    listener = GlobalHotkeyListener(on_start, on_stop)
    listener.start()
    
    try:
        input("\nPresiona Enter para salir...\n")
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()
