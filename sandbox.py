###
'''
import sys
from PyQt6.QtWidgets import QApplication, QWidget
from trigger import Effect

app = QApplication.instance() or QApplication(sys.argv)
w = Effect()
w.show()
sys.exit(app.exec())
'''
###
'''
from sampler import Inputs
import time

tracker = Inputs()
tracker.start()
while True:
    time.sleep(5)
    print(tracker.reset())
'''
###