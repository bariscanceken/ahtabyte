import pyautogui
import time
import os

def capturescreen():
    save_path = "data/screenshots"
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    img = pyautogui.screenshot()
    img = img.resize((1280, 720))
    img_path = f"{save_path}/screen_{timestamp}.jpg"
    img.save(img_path, quality=30)

    return img_path