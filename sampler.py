import pygetwindow as gw
from pynput import mouse, keyboard

###
class Inputs:
    def __init__(self):
        self.keysn = 0
        self.clickn = 0
        self.klistener = keyboard.Listener(on_press=self.keyspress)
        self.mlistener = mouse.Listener(on_click=self.clickpress)

    def start(self):
        self.klistener.start()
        self.mlistener.start()

    def keyspress(self, key):
            self.keysn += 1

    def clickpress(self, x, y, button, pressed):
            if pressed: 
                  self.clickn += 1
    
    def reset(self):
        stats = (self.keysn, self.clickn)
        self.keysn = 0
        self.clickn = 0
        return stats
    
    ###

    def windows(self):
        windows = gw.getAllWindows()
        clearwindows = []
        
        for w in windows:
            if w.title and w.visible and w.width > 0 and w.height > 0:
                if w.title not in ["Program Manager", "Ayarlar", "OmApSvcBroker"]: 
                    clearwindows.append(w.title)
        return clearwindows