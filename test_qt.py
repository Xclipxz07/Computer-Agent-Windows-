from PyQt6.QtWidgets import QApplication, QWidget
import sys

def test_qt():
    print("Starting Qt test...")
    app = QApplication(sys.argv)
    w = QWidget()
    w.setWindowTitle("Test")
    w.show()
    print("Qt window shown. Exiting test.")
    return 0

if __name__ == "__main__":
    sys.exit(test_qt())
