import threading
import time
from pynput import mouse, keyboard


class Inputs:
    def __init__(self):
        self.keysn = 0
        self.clickn = 0
        self.lock = threading.Lock()

    def keyspress(self, key):
        with self.lock:
            self.keysn += 1

    def clickpress(self, x, y, button, pressed):
        if pressed:
            with self.lock:
                self.clickn += 1

    def startc(self):
        self.klistener = keyboard.Listener(on_press=self.keyspress)
        self.mlistener = mouse.Listener(on_click=self.clickpress)

        self.klistener.start()
        self.mlistener.start()

        self.klistener.join()
        self.mlistener.join()

    def reset(self):
        with self.lock:
            stats = (self.keysn, self.clickn)
            self.keysn = 0
            self.clickn = 0
            return stats