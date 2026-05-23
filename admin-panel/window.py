33from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl

app = QApplication([])
window = QMainWindow()
browser = QWebEngineView()
window.setCentralWidget(browser)

# Cargar el dominio
browser.setUrl(QUrl("https://papoys.me"))

window.show()
app.exec()