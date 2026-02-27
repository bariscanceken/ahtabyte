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
from src.core.rag import RAGPipeline

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Signaler(QObject):
    show_effect_signal = pyqtSignal()


class Repeater:
    def __init__(self):
        self.ticks = Inputs()
        self.context_file = os.path.join(BASE_DIR, "data", "chromacontext.md")
        os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
        self.pipeline = RAGPipeline()
        self.capture_every_n = 5  # 0 yaparsan ekran analizi tamamen kapanır
        self._tick_index = 0

    def show_effect(self):
        self.effect = Effect()
        self.effect.show()

    def stream_to_context(self, signaler):
        interval = 60
        next_time = time.time()

        while True:
            try:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                active_windows = getwindows()
                key_count, mouse_count = self.ticks.reset()
                self._tick_index += 1

                img_path = None
                if self.capture_every_n and self._tick_index % self.capture_every_n == 0:
                    img_path = capturescreen()

                signaler.show_effect_signal.emit()

                text = (
                    f"TIME: {now}\n"
                    f"ACTIVE_WINDOWS: {active_windows}\n"
                    f"KEY_COUNT: {key_count}\n"
                    f"MOUSE_COUNT: {mouse_count}"
                )
                self.pipeline.ingest(text, now, img_path=img_path)

                with open(self.context_file, "a", encoding="utf-8") as f:
                    f.write(f"\n---\nENTRY_START: {now}\nSCREENSHOT_REF: {img_path or ''}\nENTRY_END\n---\n")

                print(f"[{now}] Saved.")

            except Exception as e:
                import traceback
                print(f"ERROR: {e}")
                traceback.print_exc()

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