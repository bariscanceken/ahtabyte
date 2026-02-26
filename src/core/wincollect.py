import pygetwindow as gw

def getwindows():
    windows = gw.getAllWindows()
    clearwindows = []
        
    for w in windows:
        if w.title and w.visible and w.width > 0 and w.height > 0:
            if w.title not in ["Program Manager", "Ayarlar", "OmApSvcBroker"]: 
                clearwindows.append(w.title)
    return clearwindows