###
'''
import sys
from PyQt6.QtWidgets import QApplication, QWidget
from src.ui.trigger import Effect

app = QApplication.instance() or QApplication(sys.argv)
w = Effect()
w.show()
sys.exit(app.exec())
'''
###
'''
from src.core.tickcollect import Inputs
import time

tracker = Inputs()
tracker.start()
while True:
    time.sleep(5)
    print(tracker.reset())
'''
###
'''
from src.core.wincollect import getwindows
a = getwindows()
print(a)
'''

###
'''
from src.core.visscollect import capturescreen
capturescreen()
'''
###
