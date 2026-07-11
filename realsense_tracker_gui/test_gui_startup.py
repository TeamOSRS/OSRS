import sys
from PySide6 import QtCore, QtWidgets
from main import MainWindow

def test_startup():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    
    # After 1 second, switch to calibration mode
    QtCore.QTimer.singleShot(1000, window.switch_to_calib_mode)
    
    # After 3 seconds, close the application
    QtCore.QTimer.singleShot(3000, app.quit)
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    test_startup()
