from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette

class OverlayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sound Assistant")
        
        # Window flags for transparency and overlay
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool |
            Qt.WindowTransparentForInput # Click-through
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Full screen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        # Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(50, 100, 50, 100) # Margins from edges
        
        # Left Panel
        self.left_label = QLabel("")
        self.left_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.left_label.setStyleSheet("color: cyan; background-color: rgba(0, 0, 0, 100); padding: 10px; border-radius: 10px;")
        self.left_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.left_label.setVisible(False)
        
        # Right Panel
        self.right_label = QLabel("")
        self.right_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.right_label.setStyleSheet("color: cyan; background-color: rgba(0, 0, 0, 100); padding: 10px; border-radius: 10px;")
        self.right_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.right_label.setVisible(False)
        
        layout.addWidget(self.left_label, alignment=Qt.AlignLeft)
        layout.addStretch()
        layout.addWidget(self.right_label, alignment=Qt.AlignRight)
        
        # Timer to clear text if no update
        self.clear_timer = QTimer()
        self.clear_timer.timeout.connect(self.clear_display)
        self.clear_timer.start(3000) # Clear after 3 seconds of no updates

    def update_display(self, left_text, right_text):
        if left_text:
            self.left_label.setText(left_text)
            self.left_label.setVisible(True)
            self.left_label.adjustSize()
        else:
            self.left_label.setVisible(False)
            
        if right_text:
            self.right_label.setText(right_text)
            self.right_label.setVisible(True)
            self.right_label.adjustSize()
        else:
            self.right_label.setVisible(False)
            
        # Reset clear timer
        self.clear_timer.start(3000)

    def clear_display(self):
        self.left_label.setVisible(False)
        self.right_label.setVisible(False)
