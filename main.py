import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from gui.main_window import MainWindow

def main():
    # Setup High-DPI scaling
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("OpenCut")
    app.setOrganizationName("OpenCut")

    # Set modern clean Segoe UI system font
    app_font = QFont("Segoe UI", 9)
    app_font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(app_font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
