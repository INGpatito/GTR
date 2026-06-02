zimport sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl('http://papoys.me'))
        self.browser.page().settings().setAttribute(QWebEngineSettings.ShowScrollBars, False)
        self.setCentralWidget(self.browser)
        self.showMaximized()

#sys.argv.append("--disable-gpu")
app = QApplication(sys.argv)
QApplication.setApplicationName('Papoys.me Viewer')
window = MainWindow()
app.exec_()
