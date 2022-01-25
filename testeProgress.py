import sys
from PyQt5.QtWidgets import QWidget, QApplication, QProgressBar, QPushButton
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class DownloadThread(QThread):
    taskFinished = pyqtSignal()

    def __init__(self, parent=None):
        super(DownloadThread, self).__init__(parent)

    def run(self):
        for i in range(20000):
            print(i)
        self.taskFinished.emit()


class Example(QWidget):

    def __init__(self):
        super(Example, self).__init__()

        self.initUI()

    def initUI(self):      
        # Set Progress Bard
        self.progressBar = QProgressBar(self)
        self.progressBar.setGeometry(30, 40, 200, 25)

        # Button
        self.btn = QPushButton('Start', self)
        self.btn.move(40, 80)
        self.btn.clicked.connect(self.start_download_thread)

        # Set Timer
        self.timer = QBasicTimer()
        self.step = 0

        # Display        
        self.setGeometry(300, 300, 280, 170)
        self.show()

    def start_download_thread(self):
        # Set Progress bar to 0%
        self.progressBar.setValue(0)


        #Start Thread
        self.Download = DownloadThread()
        self.Download.taskFinished.connect(self.onDownloaded)
        self.onDownloading()
        self.Download.start()    

    def onDownloading(self):
        #start the timer
        self.progressBar.show()
        self.timerSwitch()


    def timerSwitch(self):
        # Turn timer off or on
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start(2, self)

    def onDownloaded(self):
        # Stop the timer
        self.timerSwitch()
    # progress bar 100%
        self.progressBar.setValue(1)
        self.progressBar.setRange(0, 1)

    def timerEvent(self, e): 
        if self.step >= 100:
            self.timer.stop()
            # self.Download.quit()

            return
        self.step = self.step + 1
        self.progressBar.setValue(self.step)


ex = Example()
