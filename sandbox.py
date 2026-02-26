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
'''
from src.core.rag import RAGPipeline

pipeline = RAGPipeline()
pipeline.ingest("ACTIVE_WINDOWS: VS Code\nKEYBOARD_TICKS: 10\nMOUSE_TICKS: 5", "2026-02-26 14:00:00")
print("Ingest test OK")
'''
###
'''
from src.core.rag import RAGPipeline

pipeline = RAGPipeline()
report = pipeline.generate_report("2026-02-26 14:00:00", "2026-02-26 15:00:00")
print(report)
'''
###