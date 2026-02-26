import sys 
import os 
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import threading
import time
from datetime import datetime

from src.core.tickcollect import Inputs
from src.core.wincollect import getwindows
from src.core.visscollect import capturescreen
from src.ui.trigger import Effect

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal
import sys


class Signaler(QObject):
    show_effect_signal = pyqtSignal()


class Repeater:
    def __init__(self):
        self.ticks = Inputs()
        self.context_file = "data/chromacontext.md"
        os.makedirs("data", exist_ok=True)

    def show_effect(self):
        self.effect = Effect()  # self ile tut, silinmesin
        self.effect.show()

    def stream_to_context(self, signaler):
        interval = 60
        next_time = time.time()

        while True:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            active_windows = getwindows()
            key_count, mouse_count = self.ticks.reset()
            img_path = capturescreen()

            signaler.show_effect_signal.emit()

            context_block = f"""
---
ENTRY_START: {now}
ACTIVE_WINDOWS: {', '.join(active_windows)}
KEYBOARD_TICKS: {key_count}
MOUSE_TICKS: {mouse_count}
SCREENSHOT_REF: {img_path}
ENTRY_END
---
"""
            with open(self.context_file, "a", encoding="utf-8") as f:
                f.write(context_block)

            print(f"[{now}] Veri eklendi.")

            next_time += interval
            sleep_time = next_time - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

    def start(self):
        app = QApplication(sys.argv)

        signaler = Signaler()
        signaler.show_effect_signal.connect(self.show_effect)

        listener_thread = threading.Thread(target=self.ticks.startc, daemon=True)
        listener_thread.start()

        stream_thread = threading.Thread(target=self.stream_to_context, args=(signaler,), daemon=True)
        stream_thread.start()

        sys.exit(app.exec())


if __name__ == "__main__":
    Repeater().start()