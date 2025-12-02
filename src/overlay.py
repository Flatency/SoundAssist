from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QHBoxLayout, QGridLayout, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt5.QtGui import QFont, QColor, QPalette, QPainter, QPen, QBrush
import math

class RadarWidget(QWidget):
    def __init__(self, parent=None, size=300):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.dots = [] # List of (angle, distance, label, confidence)
        self.channel_levels = [] # List of (angle, level)
        self.mode = 'semi' # 'semi' or 'full'

    def set_size(self, size):
        self.setFixedSize(size, size)
        self.update()

    def update_dots(self, dots, mode='semi', channel_levels=None):
        self.dots = dots
        self.mode = mode
        if channel_levels is not None:
            self.channel_levels = channel_levels
        else:
            self.channel_levels = []
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw Radar Background
        center = QPoint(self.width() // 2, self.height()) if self.mode == 'semi' else QPoint(self.width() // 2, self.height() // 2)
        radius = (min(self.width() // 2, self.height()) - 20) if self.mode == 'semi' else (min(self.width(), self.height()) // 2 - 20)
        
        painter.setPen(QPen(QColor(0, 255, 255, 100), 2))
        painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
        
        if self.mode == 'semi':
            # Draw semi-circle
            painter.drawPie(center.x() - radius, center.y() - radius, radius * 2, radius * 2, 0, 180 * 16)
            
            # Draw grid lines
            painter.setPen(QPen(QColor(0, 255, 255, 50), 1))
            painter.drawPie(center.x() - radius//2, center.y() - radius//2, radius, radius, 0, 180 * 16)
            painter.drawLine(center, QPoint(center.x() - int(radius * math.cos(math.pi/4)), center.y() - int(radius * math.sin(math.pi/4))))
            painter.drawLine(center, QPoint(center.x() + int(radius * math.cos(math.pi/4)), center.y() - int(radius * math.sin(math.pi/4))))
        else:
            # Draw full circle
            painter.drawEllipse(center, radius, radius)
            
            # Draw grid lines
            painter.setPen(QPen(QColor(0, 255, 255, 50), 1))
            painter.drawEllipse(center, radius//2, radius//2)
            painter.drawLine(center.x() - radius, center.y(), center.x() + radius, center.y())
            painter.drawLine(center.x(), center.y() - radius, center.x(), center.y() + radius)

        # Draw Channel Levels
        if self.channel_levels:
            painter.setPen(QPen(QColor(0, 255, 0, 200), 4))
            max_bar_len = 20
            
            for angle_deg, level in self.channel_levels:
                # Convert angle to radians for drawing
                # Angle 0 is Up (North), 90 is Right.
                # Math: x = sin(theta), y = -cos(theta)
                
                # Clamp level
                level = min(max(level, 0), 1.0)
                bar_len = level * max_bar_len
                
                if bar_len < 1: continue
                
                rad = math.radians(angle_deg)
                
                # Start point on circle edge
                start_x = center.x() + radius * math.sin(rad)
                start_y = center.y() - radius * math.cos(rad)
                
                # End point outwards
                end_x = center.x() + (radius + bar_len) * math.sin(rad)
                end_y = center.y() - (radius + bar_len) * math.cos(rad)
                
                painter.drawLine(QPoint(int(start_x), int(start_y)), QPoint(int(end_x), int(end_y)))

        # Draw Dots
        for angle_val, dist_val, label, conf in self.dots:
            # angle_val is [-1, 1]. 
            # In 'semi' mode: -1 is Left (180 deg), 1 is Right (0 deg), 0 is Center (90 deg)
            # In 'full' mode: angle_val is radians? Or degrees? Let's use degrees for simplicity in main.py and convert here.
            # Actually, let's standardize: angle_val is always in degrees, 0 is Front/Right?
            # Let's stick to the previous convention for semi: -1 to 1.
            # For full, let's use degrees: 0 is Front, 90 Right, 180 Back, -90 Left.
            
            if self.mode == 'semi':
                angle_rad = (1 - angle_val) * (math.pi / 2)
            else:
                # Full mode: angle_val is degrees. 0 is North (Up).
                # Screen coords: Y is down.
                # 0 deg (Front) -> Up -> (0, -r)
                # 90 deg (Right) -> Right -> (r, 0)
                # 180 deg (Back) -> Down -> (0, r)
                # -90 deg (Left) -> Left -> (-r, 0)
                # Math: x = r * sin(theta), y = -r * cos(theta)
                angle_rad = math.radians(angle_val)
                
            # Distance
            r = dist_val * radius
            
            if self.mode == 'semi':
                x = center.x() + r * math.cos(angle_rad)
                y = center.y() - r * math.sin(angle_rad)
            else:
                x = center.x() + r * math.sin(angle_rad)
                y = center.y() - r * math.cos(angle_rad)
            
            # Color based on confidence
            if conf > 0.7:
                color = QColor(0, 255, 0) # Green
            elif conf > 0.4:
                color = QColor(255, 255, 0) # Yellow
            else:
                color = QColor(255, 0, 0) # Red
                
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPoint(int(x), int(y)), 8, 8)
            
            # Draw Label
            painter.setPen(QPen(Qt.white))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(int(x) + 10, int(y), label)


class OverlayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sound Assistant Overlay")
        
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
        
        # Main Layout (Grid Layout for better positioning)
        self.main_layout = QGridLayout(central_widget)
        self.main_layout.setContentsMargins(50, 20, 50, 50)
        
        # Configure Grid Rows/Cols
        # Row 0: Top, Row 1: Middle (Expand), Row 2: Bottom
        # Col 0: Left, Col 1: Center, Col 2: Right
        self.main_layout.setRowStretch(0, 0)
        self.main_layout.setRowStretch(1, 1)
        self.main_layout.setRowStretch(2, 0)
        self.main_layout.setColumnStretch(0, 1)
        self.main_layout.setColumnStretch(1, 1)
        self.main_layout.setColumnStretch(2, 1)
        
        # Debug Label (Top Center - Row 0, Col 1)
        debug_container = QWidget()
        debug_container.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        debug_layout = QVBoxLayout(debug_container)
        debug_layout.setContentsMargins(0, 0, 0, 0)
        debug_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        
        self.debug_label = QLabel("")
        self.debug_label.setFont(QFont("Consolas", 10))
        self.debug_label.setStyleSheet("color: yellow; background-color: rgba(0, 0, 0, 150); padding: 5px;")
        self.debug_label.setAlignment(Qt.AlignHCenter)
        self.debug_label.setVisible(False)
        debug_layout.addWidget(self.debug_label)
        self.main_layout.addWidget(debug_container, 0, 1)
        
        # Left Panel (Middle Left - Row 1, Col 0)
        left_container = QWidget()
        left_container.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.left_label = QLabel("")
        self.left_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.left_label.setStyleSheet("color: cyan; background-color: rgba(0, 0, 0, 100); padding: 10px; border-radius: 10px;")
        self.left_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.left_label.setVisible(False)
        left_layout.addWidget(self.left_label)
        self.main_layout.addWidget(left_container, 1, 0)
        
        # Right Panel (Middle Right - Row 1, Col 2)
        right_container = QWidget()
        right_container.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.right_label = QLabel("")
        self.right_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.right_label.setStyleSheet("color: cyan; background-color: rgba(0, 0, 0, 100); padding: 10px; border-radius: 10px;")
        self.right_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.right_label.setVisible(False)
        right_layout.addWidget(self.right_label)
        self.main_layout.addWidget(right_container, 1, 2)
        
        # Radar (Initially Bottom Center - Row 2, Col 1)
        self.radar = RadarWidget()
        self.radar.setVisible(False)
        self.main_layout.addWidget(self.radar, 2, 1, Qt.AlignBottom | Qt.AlignHCenter)
        
        # Timer to clear text if no update
        self.clear_timer = QTimer()
        self.clear_timer.timeout.connect(self.clear_display)
        self.clear_timer.start(3000) # Clear after 3 seconds of no updates
        
        self.current_radar_mode = 'semi'

    def update_layout_params(self, position, size):
        # Update Radar Size
        # Update Radar Size
        self.radar.set_size(size)
        
        # Update Radar Position
        # Remove radar from layout and re-add with correct alignment
        self.main_layout.removeWidget(self.radar)
        
        row, col = 2, 1 # Default Bottom Center
        alignment = Qt.AlignBottom | Qt.AlignHCenter
        
        if position == "Top Left":
            row, col = 0, 0
            alignment = Qt.AlignTop | Qt.AlignLeft
        elif position == "Top Center":
            row, col = 0, 1
            alignment = Qt.AlignTop | Qt.AlignHCenter
        elif position == "Top Right":
            row, col = 0, 2
            alignment = Qt.AlignTop | Qt.AlignRight
        elif position == "Bottom Left":
            row, col = 2, 0
            alignment = Qt.AlignBottom | Qt.AlignLeft
        elif position == "Bottom Center":
            row, col = 2, 1
            alignment = Qt.AlignBottom | Qt.AlignHCenter
        elif position == "Bottom Right":
            row, col = 2, 2
            alignment = Qt.AlignBottom | Qt.AlignRight
            
        self.main_layout.addWidget(self.radar, row, col, alignment)

    def update_display(self, left_text, right_text, radar_dots=None, debug_info=None, radar_mode='semi', channel_levels=None):
        self.current_radar_mode = radar_mode
        
        if left_text:
            self.left_label.setText(left_text)
            self.left_label.setVisible(True)
            # self.left_label.adjustSize()
        else:
            self.left_label.setVisible(False)
            
        if right_text:
            self.right_label.setText(right_text)
            self.right_label.setVisible(True)
            # self.right_label.adjustSize()
        else:
            self.right_label.setVisible(False)
            
        if radar_dots is not None and self.radar.isVisible():
            self.radar.update_dots(radar_dots, mode=radar_mode, channel_levels=channel_levels)
            
        if debug_info:
            self.debug_label.setText(debug_info)
            self.debug_label.setVisible(True)
            # self.debug_label.adjustSize()
        else:
            self.debug_label.setVisible(False)
            
        # Reset clear timer
        self.clear_timer.start(3000)

    def clear_display(self):
        self.left_label.setVisible(False)
        self.right_label.setVisible(False)
        self.radar.update_dots([], mode=self.current_radar_mode)
        # Don't clear debug info immediately, or maybe yes?
        # self.debug_label.setVisible(False)

    def set_radar_enabled(self, enabled):
        self.radar.setVisible(enabled)
