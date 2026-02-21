import sys
from PyQt6.QtWidgets import QApplication, QLabel, QWidget
from PyQt6.QtGui import QMovie
from PyQt6.QtCore import Qt, QTimer
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
gif_path = os.path.join(base_dir, "media", "octosprite.gif")

class Effect(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.label = QLabel(self)
        self.movie = QMovie(gif_path)
        self.label.setMovie(self.movie)
        
        self.movie.jumpToFrame(0) 
        gifsize = self.movie.currentImage().size()
        self.resize(gifsize)
        self.label.setFixedSize(gifsize)
        
        self.movie.start()

        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.width() - gifsize.width() - 20
        y = screen.height() - gifsize.height() - 20 
        self.move(x, y)

        QTimer.singleShot(5000, self.close)

    def closeEvent(self, event):

        if hasattr(self, 'movie'):
            self.movie.stop()
        QApplication.quit()
        event.accept()
        