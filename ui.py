from PyQt6.QtWidgets import QWidget, QApplication, QLineEdit, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QColor, QPainter, QBrush, QRadialGradient, QPen
import sys
import math

class SiriOverlay(QWidget):
    text_input_received = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Hidden input for Voice Access
        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText("Voice Access Input...")
        # Make it effectively invisible but functional
        self.input_field.setStyleSheet("background: transparent; border: none; color: transparent; font-size: 1px;")
        self.input_field.setFixedWidth(1)
        self.input_field.move(-10, -10)
        self.input_field.returnPressed.connect(self._on_text_entered)

        # Timer to detect when Voice Access finishes typing (if no Enter is sent)
        self.input_timer = QTimer()
        self.input_timer.setSingleShot(True)
        self.input_timer.timeout.connect(self._on_text_entered)
        self.input_field.textChanged.connect(lambda: self.input_timer.start(1000)) # 1s silence trigger

        # Full screen overlay or bottom center?
        screen = QApplication.primaryScreen().geometry()
        width = 300
        height = 300
        self.setGeometry(
            (screen.width() - width) // 2,
            screen.height() - height - 50, # 50px from bottom
            width, 
            height
        )
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(30) # 30ms for smooth animation
        
        self.angle = 0
        self.is_listening = False
        self.is_speaking = False
        self.is_wake_word = False
        self.amplitude = 10 # Base amplitude

    def _on_text_entered(self):
        text = self.input_field.text().strip()
        if text:
            print(f"[UI] Input received via Voice Access: {text}")
            self.text_input_received.emit(text)
            self.input_field.clear()
            self.input_timer.stop()

    def set_state(self, state):
        """ 'listening', 'speaking', 'idle', 'processing', 'wake_word' """
        if state == 'listening':
            self.is_listening = True
            self.is_speaking = False
            self.is_wake_word = False
            # Focus input field for Voice Access
            self.input_field.setFocus()
            self.input_field.clear()
        elif state == 'speaking':
            self.is_listening = False
            self.is_speaking = True
            self.is_wake_word = False
            self.input_field.clearFocus()
        elif state == 'wake_word':
            self.is_listening = False
            self.is_speaking = False
            self.is_wake_word = True
        else:
            self.is_listening = False
            self.is_speaking = False
            self.is_wake_word = False

    def update_animation(self):
        self.angle += 0.1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Dynamic Pulse
        if self.is_listening:
            # Active listening - bright and pulsing
            pulse = 10 * math.sin(self.angle * 2)
            base_radius = 80
            core_color = QColor(255, 255, 255, 220)
            mid_color = QColor(0, 255, 255, 150)  # Cyan
            outer_color = QColor(138, 43, 226, 120)  # Purple
        elif self.is_speaking:
            # Speaking - faster pulse
            pulse = 15 * math.sin(self.angle * 5)
            base_radius = 90
            core_color = QColor(255, 255, 255, 220)
            mid_color = QColor(255, 100, 255, 150)  # Pink
            outer_color = QColor(138, 43, 226, 120)  # Purple
        elif self.is_wake_word:
            # Waiting for wake word - subtle pulse, dimmer
            pulse = 5 * math.sin(self.angle * 0.5)
            base_radius = 50
            core_color = QColor(200, 200, 200, 150)
            mid_color = QColor(100, 150, 255, 100)  # Soft blue
            outer_color = QColor(50, 100, 200, 80)  # Darker blue
        else: # Idle
            pulse = 5 * math.sin(self.angle)
            base_radius = 60
            core_color = QColor(255, 255, 255, 180)
            mid_color = QColor(0, 200, 255, 120)
            outer_color = QColor(100, 100, 200, 100)

        radius = base_radius + pulse
        
        # Gradient Orb
        gradient = QRadialGradient(center_x, center_y, radius)
        
        gradient.setColorAt(0, core_color)
        gradient.setColorAt(0.4, mid_color)
        gradient.setColorAt(0.7, outer_color)
        gradient.setColorAt(1, QColor(0, 0, 0, 0)) # Transparent edges
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(center_x - radius), int(center_y - radius), int(radius * 2), int(radius * 2))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SiriOverlay()
    window.show()
    sys.exit(app.exec())

