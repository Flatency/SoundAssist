from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QCheckBox, QSlider, QPushButton, QSystemTrayIcon, 
                             QMenu, QAction, QStyle, QGroupBox, QDoubleSpinBox, QSpinBox, QComboBox, QRadioButton, QButtonGroup, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
import config
from capturer import AudioCapturer

class SettingsWindow(QWidget):
    config_updated = pyqtSignal(dict)
    close_app = pyqtSignal()

    def closeEvent(self, event):
        self.quit_application()
        event.accept()

    def __init__(self, current_config):
        super().__init__()
        self.config = current_config
        self.setWindowTitle("Sound Assistant Settings")
        self.resize(400, 650)
        
        layout = QVBoxLayout()
        
        # --- Model Settings ---
        model_group = QGroupBox("Model Settings")
        model_layout = QVBoxLayout()
        
        # GPU Toggle
        self.gpu_check = QCheckBox("Use GPU (Requires CUDA, Restart Required)")
        self.gpu_check.setChecked(self.config["use_gpu"])
        self.gpu_check.stateChanged.connect(self.update_config)
        model_layout.addWidget(self.gpu_check)
        
        # Chunk Duration
        chunk_layout = QHBoxLayout()
        chunk_layout.addWidget(QLabel("Time Slice (s):"))
        self.chunk_slider = QSlider(Qt.Horizontal)
        self.chunk_slider.setRange(1, 30) # 0.1s to 3.0s
        self.chunk_slider.setValue(int(self.config["chunk_duration"] * 10))
        self.chunk_label = QLabel(f"{self.config['chunk_duration']:.1f}")
        self.chunk_slider.valueChanged.connect(lambda v: self.chunk_label.setText(f"{v/10:.1f}"))
        self.chunk_slider.valueChanged.connect(self.update_config)
        chunk_layout.addWidget(self.chunk_slider)
        chunk_layout.addWidget(self.chunk_label)
        model_layout.addLayout(chunk_layout)
        
        # Top-K
        topk_layout = QHBoxLayout()
        topk_layout.addWidget(QLabel("Top-K Results:"))
        self.topk_spin = QSpinBox()
        self.topk_spin.setRange(1, 10)
        self.topk_spin.setValue(self.config["top_k"])
        self.topk_spin.valueChanged.connect(self.update_config)
        topk_layout.addWidget(self.topk_spin)
        model_layout.addLayout(topk_layout)
        
        # Confidence Threshold
        conf_layout = QHBoxLayout()
        conf_layout.addWidget(QLabel("Confidence Threshold:"))
        self.conf_slider = QSlider(Qt.Horizontal)
        self.conf_slider.setRange(0, 100)
        self.conf_slider.setValue(int(self.config["confidence_threshold"] * 100))
        self.conf_label = QLabel(f"{self.config['confidence_threshold']:.2f}")
        self.conf_slider.valueChanged.connect(lambda v: self.conf_label.setText(f"{v/100:.2f}"))
        self.conf_slider.valueChanged.connect(self.update_config)
        conf_layout.addWidget(self.conf_slider)
        conf_layout.addWidget(self.conf_label)
        model_layout.addLayout(conf_layout)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # --- Audio Processing ---
        audio_group = QGroupBox("Audio Processing")
        audio_layout = QVBoxLayout()

        # Audio Device Selection
        device_layout = QVBoxLayout()
        device_layout.addWidget(QLabel("Input Device (Restart Required):"))
        self.device_combo = QComboBox()
        self.device_combo.addItem("Default System Loopback", None)
        
        # Populate devices
        devices = AudioCapturer.get_devices()
        current_device = self.config.get("audio_device")
        
        for dev in devices:
            self.device_combo.addItem(dev, dev)
            if current_device and dev == current_device:
                self.device_combo.setCurrentText(dev)
        
        self.device_combo.currentIndexChanged.connect(self.update_config)
        device_layout.addWidget(self.device_combo)
        audio_layout.addLayout(device_layout)

        # Channel Mapping
        map_layout = QHBoxLayout()
        map_layout.addWidget(QLabel("Channel Map:"))
        self.map_combo = QComboBox()
        self.map_combo.addItems([
            "Standard", 
            "Alternative (C/LFE Last)", 
            "Side 5.1", 
            "VB-Cable (Fix Back->Front)",
            "7.1 (Side/Back Swapped)"
        ])
        self.map_combo.setCurrentText(self.config.get("channel_map", "Standard"))
        self.map_combo.currentTextChanged.connect(self.update_config)
        map_layout.addWidget(self.map_combo)
        audio_layout.addLayout(map_layout)
        
        # Normalization
        self.norm_check = QCheckBox("Enable Normalization")
        self.norm_check.setChecked(self.config["normalize_audio"])
        self.norm_check.stateChanged.connect(self.toggle_norm_slider)
        self.norm_check.stateChanged.connect(self.update_config)
        audio_layout.addWidget(self.norm_check)
        
        # Hamming Window
        self.hamming_check = QCheckBox("Apply Hamming Window")
        self.hamming_check.setChecked(self.config["apply_hamming"])
        self.hamming_check.stateChanged.connect(self.update_config)
        audio_layout.addWidget(self.hamming_check)
        
        # Norm Threshold
        norm_thresh_layout = QHBoxLayout()
        norm_thresh_layout.addWidget(QLabel("Silence Threshold:"))
        self.norm_slider = QSlider(Qt.Horizontal)
        self.norm_slider.setRange(0, 100) # 0.00 to 0.10
        self.norm_slider.setValue(int(self.config["normalization_threshold"] * 1000))
        self.norm_label = QLabel(f"{self.config['normalization_threshold']:.3f}")
        self.norm_slider.valueChanged.connect(lambda v: self.norm_label.setText(f"{v/1000:.3f}"))
        self.norm_slider.valueChanged.connect(self.update_config)
        self.norm_slider.setEnabled(self.config["normalize_audio"])
        norm_thresh_layout.addWidget(self.norm_slider)
        norm_thresh_layout.addWidget(self.norm_label)
        audio_layout.addLayout(norm_thresh_layout)
        
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)
        
        # --- Display Settings ---
        display_group = QGroupBox("Display Settings")
        display_layout = QVBoxLayout()
        
        self.radar_check = QCheckBox("Enable Radar View")
        self.radar_check.setChecked(self.config["enable_radar"])
        self.radar_check.stateChanged.connect(self.update_config)
        display_layout.addWidget(self.radar_check)

        self.levels_check = QCheckBox("Show Channel Levels")
        self.levels_check.setChecked(self.config.get("show_channel_levels", False))
        self.levels_check.stateChanged.connect(self.update_config)
        display_layout.addWidget(self.levels_check)
        
        # Radar Position
        pos_group = QGroupBox("Radar Position")
        pos_layout = QVBoxLayout()
        self.pos_group = QButtonGroup(self)
        
        positions = ["Top Left", "Top Center", "Top Right", 
                     "Bottom Left", "Bottom Center", "Bottom Right"]
        
        # Grid layout for positions might be better, but let's stick to simple flow or grid
        # Let's use a grid layout for radio buttons
        from PyQt5.QtWidgets import QGridLayout
        pos_grid = QGridLayout()
        
        current_pos = self.config.get("radar_position", "Bottom Center")
        
        row = 0
        col = 0
        for pos in positions:
            rb = QRadioButton(pos)
            if pos == current_pos:
                rb.setChecked(True)
            self.pos_group.addButton(rb)
            self.pos_group.buttonToggled.connect(self.update_config)
            pos_grid.addWidget(rb, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1
        
        pos_layout.addLayout(pos_grid)
        display_layout.addWidget(pos_group)
        pos_group.setLayout(pos_layout)

        # Radar Size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Radar Size:"))
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(100, 600)
        self.size_slider.setValue(self.config.get("radar_size", 300))
        self.size_label = QLabel(f"{self.size_slider.value()} px")
        self.size_slider.valueChanged.connect(lambda v: self.size_label.setText(f"{v} px"))
        self.size_slider.valueChanged.connect(self.update_config)
        size_layout.addWidget(self.size_slider)
        size_layout.addWidget(self.size_label)
        display_layout.addLayout(size_layout)

        self.debug_check = QCheckBox("Show Debug Info")
        self.debug_check.setChecked(self.config["show_debug"])
        self.debug_check.stateChanged.connect(self.update_config)
        display_layout.addWidget(self.debug_check)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        # --- Performance ---
        perf_group = QGroupBox("Performance")
        perf_layout = QVBoxLayout()
        self.perf_label = QLabel("Latency: N/A")
        perf_layout.addWidget(self.perf_label)
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        
        layout.addStretch()
        
        # Save Button (Auto-save is implemented, but explicit button is nice)
        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        self.setLayout(layout)
        
        # System Tray
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
        
        tray_menu = QMenu()
        show_action = QAction("Show Settings", self)
        show_action.triggered.connect(self.show)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def toggle_norm_slider(self, state):
        self.norm_slider.setEnabled(state == Qt.Checked)

    def update_config(self, *args):
        self.config["use_gpu"] = self.gpu_check.isChecked()
        self.config["chunk_duration"] = self.chunk_slider.value() / 10.0
        self.config["top_k"] = self.topk_spin.value()
        self.config["confidence_threshold"] = self.conf_slider.value() / 100.0
        self.config["enable_radar"] = self.radar_check.isChecked()
        self.config["normalize_audio"] = self.norm_check.isChecked()
        self.config["normalization_threshold"] = self.norm_slider.value() / 1000.0
        self.config["apply_hamming"] = self.hamming_check.isChecked()
        self.config["show_debug"] = self.debug_check.isChecked()
        self.config["show_channel_levels"] = self.levels_check.isChecked()
        self.config["audio_device"] = self.device_combo.currentData()
        self.config["channel_map"] = self.map_combo.currentText()
        
        # Get checked radio button text
        checked_btn = self.pos_group.checkedButton()
        if checked_btn:
            self.config["radar_position"] = checked_btn.text()
            
        self.config["radar_size"] = self.size_slider.value()
        
        self.config_updated.emit(self.config)

    def save_settings(self):
        config.save_config(self.config)

    def update_performance(self, latency):
        self.perf_label.setText(f"Latency: {latency*1000:.1f} ms")

    def quit_application(self):
        self.save_settings()
        self.close_app.emit()
        QApplication.quit()
