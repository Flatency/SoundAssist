import sys
import threading
import numpy as np
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal
import warnings
import math

# Suppress warnings globally
warnings.filterwarnings("ignore", message=".*data discontinuity.*")

from classifier import AudioClassifier
from capturer import AudioCapturer
from overlay import OverlayWindow
from gui import SettingsWindow
import config

class AudioWorker(QObject):
    update_signal = pyqtSignal(str, str, list, str, str, list) # left_text, right_text, radar_dots, debug_info, radar_mode, channel_levels
    perf_signal = pyqtSignal(float)

    def __init__(self, initial_config):
        super().__init__()
        self.running = True
        self.config = initial_config
        self.classifier = None
        self.capturer = None
        self.lock = threading.Lock()
        self.dot_history = {} # name -> {'angle': val, 'dist': val}

    def update_config(self, new_config):
        with self.lock:
            # Check if device changed
            if self.classifier and self.config["use_gpu"] != new_config["use_gpu"]:
                self.classifier.set_device(new_config["use_gpu"])
            
            # Check if chunk duration changed (requires capturer restart? No, capturer reads config)
            if self.capturer:
                self.capturer.chunk_duration = new_config["chunk_duration"]
                
            self.config = new_config

    def run(self):
        print("Initializing Audio Capturer...")
        self.capturer = AudioCapturer(
            chunk_duration=self.config["chunk_duration"],
            device_name=self.config.get("audio_device")
        )
        
        print("Initializing Classifier...")
        self.classifier = AudioClassifier(use_gpu=self.config["use_gpu"])
        
        print("Starting Audio Loop...")
        for audio_chunk in self.capturer.capture_loop():
            if not self.running:
                break
            
            with self.lock:
                cfg = self.config.copy()
            
            # audio_chunk: [frames, channels]
            channels = audio_chunk.shape[1]
            
            # Apply Hamming Window
            if cfg["apply_hamming"]:
                # Apply window per channel
                window = np.hamming(audio_chunk.shape[0])
                # Broadcast window to all channels
                audio_chunk = audio_chunk * window[:, np.newaxis]

            # Normalization
            if cfg["normalize_audio"]:
                max_val = np.max(np.abs(audio_chunk))
                if max_val > cfg["normalization_threshold"]:
                    audio_chunk = audio_chunk / max_val
                # Else: too quiet, don't boost noise
            
            # Check for silence (using normalization threshold as silence threshold too)
            rms = np.sqrt(np.mean(audio_chunk**2))
            if rms < cfg["normalization_threshold"]: 
                continue
                
            left_text = ""
            right_text = ""
            radar_dots = []
            radar_mode = 'semi'
            channel_levels = []
            
            total_latency = 0
            
            # --- Channel Mapping Setup ---
            channel_angles = {}
            if channels <= 2:
                if channels >= 1: channel_angles[0] = -45 # Left
                if channels >= 2: channel_angles[1] = 45  # Right
            else:
                # Default Standard Mapping
                # 0: FL, 1: FR, 2: C, 3: LFE, 4: BL, 5: BR, 6: SL, 7: SR
                channel_angles = {
                    0: -45,  # FL
                    1: 45,   # FR
                    2: 0,    # Center
                    4: -135, # BL
                    5: 135,  # BR
                }
                if channels >= 8:
                    channel_angles[6] = -90 # SL
                    channel_angles[7] = 90  # SR

                # Apply Custom Mapping
                map_mode = cfg.get("channel_map", "Standard")
                
                if map_mode == "Alternative (C/LFE Last)" or map_mode == "VB-Cable (Fix Back->Front)":
                    # 0: FL, 1: FR, 2: BL, 3: BR, 4: C, 5: LFE
                    channel_angles = {
                        0: -45,  # FL
                        1: 45,   # FR
                        2: -135, # BL
                        3: 135,  # BR
                        4: 0     # Center
                    }
                    if channels >= 8:
                        channel_angles[6] = -90
                        channel_angles[7] = 90
                        
                elif map_mode == "Side 5.1":
                    # 0: FL, 1: FR, 2: C, 3: LFE, 4: SL, 5: SR
                    channel_angles = {
                        0: -45, # FL
                        1: 45,  # FR
                        2: 0,   # Center
                        4: -90, # SL
                        5: 90   # SR
                    }
                    
                elif map_mode == "7.1 (Side/Back Swapped)":
                    # Standard but swap 4/5 with 6/7
                    # 0: FL, 1: FR, 2: C, 3: LFE, 4: SL, 5: SR, 6: BL, 7: BR
                    channel_angles = {
                        0: -45,  # FL
                        1: 45,   # FR
                        2: 0,    # Center
                        4: -90,  # SL (was BL)
                        5: 90,   # SR (was BR)
                    }
                    if channels >= 8:
                        channel_angles[6] = -135 # BL (was SL)
                        channel_angles[7] = 135  # BR (was SR)

            # --- Channel Levels Calculation ---
            if cfg.get("show_channel_levels", False):
                for ch_idx in range(channels):
                    if ch_idx in channel_angles:
                        # Calculate RMS for this channel
                        ch_data = audio_chunk[:, ch_idx]
                        ch_rms = np.sqrt(np.mean(ch_data**2))
                        channel_levels.append((channel_angles[ch_idx], ch_rms))

            # --- Classification Logic ---
            
            # Case 1: Stereo (2 Channels) or Mono (1 Channel)
            if channels <= 2:
                radar_mode = 'semi'
                
                # Process Left Channel
                left_results = []
                if channels >= 1:
                    left_audio = audio_chunk[:, 0]
                    left_results, lat = self.classifier.predict(left_audio, top_k=cfg["top_k"])
                    total_latency += lat
                    
                    valid_results = [f"{name} ({score:.2f})" for name, score in left_results 
                                     if score > cfg["confidence_threshold"] and name != 'Silence']
                    if valid_results:
                        left_text = "< " + "\n< ".join(valid_results)
                
                # Process Right Channel
                right_results = []
                if channels >= 2:
                    right_audio = audio_chunk[:, 1]
                    right_results, lat = self.classifier.predict(right_audio, top_k=cfg["top_k"])
                    total_latency += lat
                    
                    valid_results = [f"{name} ({score:.2f})" for name, score in right_results 
                                     if score > cfg["confidence_threshold"] and name != 'Silence']
                    if valid_results:
                        right_text = "\n".join(valid_results) + " >"
                
                # Radar Logic for Stereo
                if cfg["enable_radar"]:
                    all_preds = {} # name -> {'left': score, 'right': score}
                    
                    for name, score in left_results:
                        if score > cfg["confidence_threshold"]:
                            if name not in all_preds: all_preds[name] = {'left': 0, 'right': 0}
                            all_preds[name]['left'] = score
                            
                    for name, score in right_results:
                        if score > cfg["confidence_threshold"]:
                            if name not in all_preds: all_preds[name] = {'left': 0, 'right': 0}
                            all_preds[name]['right'] = score
                    
                    for name, scores in all_preds.items():
                        l = scores['left']
                        r = scores['right']
                        
                        # Position: -1 (Left) to 1 (Right)
                        if l + r > 0:
                            pos = (r - l) / (l + r)
                        else:
                            pos = 0
                        
                        dist = max(l, r)
                        radar_dots.append((pos, dist, name, dist))

            # Case 2: Surround Sound (> 2 Channels)
            else:
                radar_mode = 'full'
                
                # Aggregate results per class
                class_vectors = {} # name -> {'x': 0, 'y': 0, 'max_score': 0}
                
                for ch_idx, angle in channel_angles.items():
                    if ch_idx < channels:
                        audio = audio_chunk[:, ch_idx]
                        results, lat = self.classifier.predict(audio, top_k=cfg["top_k"])
                        total_latency += lat
                        
                        for name, score in results:
                            if score > cfg["confidence_threshold"] and name != 'Silence':
                                if name not in class_vectors:
                                    class_vectors[name] = {'x': 0, 'y': 0, 'max_score': 0}
                                
                                # Add vector component
                                rad = math.radians(angle)
                                # x is right (sin), y is up (cos)
                                # But in screen coords y is down.
                                # Let's stick to standard math (x right, y up) and convert later
                                class_vectors[name]['x'] += score * math.sin(rad)
                                class_vectors[name]['y'] += score * math.cos(rad)
                                class_vectors[name]['max_score'] = max(class_vectors[name]['max_score'], score)

                # Convert vectors to radar dots
                for name, vec in class_vectors.items():
                    x = vec['x']
                    y = vec['y']
                    mag = math.sqrt(x*x + y*y)
                    
                    if mag > 0:
                        # Calculate angle
                        # atan2(y, x) gives angle from x-axis (Right).
                        # We want angle from Y-axis (Up/Front).
                        # Standard atan2: 0 is Right, 90 is Up.
                        # Our angle definition: 0 is Up, 90 is Right.
                        # So our angle = 90 - math.degrees(atan2(y, x))
                        angle_deg = 90 - math.degrees(math.atan2(y, x))
                        
                        # Normalize angle to [-180, 180]
                        if angle_deg > 180: angle_deg -= 360
                        if angle_deg < -180: angle_deg += 360
                        
                        # Distance: use max_score as distance proxy
                        dist = vec['max_score']
                        
                        radar_dots.append((angle_deg, dist, name, dist))
                        
                        # Also populate text for Left/Right based on angle
                        if -90 <= angle_deg < 0 or angle_deg < -90: # Left side
                             left_text += f"{name} ({dist:.2f})\n"
                        if 0 < angle_deg <= 90 or angle_deg > 90: # Right side
                             right_text += f"{name} ({dist:.2f})\n"

            # --- Smoothing Logic ---
            smoothed_dots = []
            alpha = 0.3 # Smoothing factor
            
            current_names = set()
            
            for angle, dist, name, score in radar_dots:
                current_names.add(name)
                if name in self.dot_history:
                    last_angle = self.dot_history[name]['angle']
                    last_dist = self.dot_history[name]['dist']
                    
                    # Smooth Distance
                    new_dist = alpha * dist + (1 - alpha) * last_dist
                    
                    # Smooth Angle
                    if radar_mode == 'full':
                        # Angle difference handling for circular wrap-around
                        diff = angle - last_angle
                        if diff > 180: diff -= 360
                        if diff < -180: diff += 360
                        new_angle = last_angle + alpha * diff
                        # Normalize
                        if new_angle > 180: new_angle -= 360
                        if new_angle <= -180: new_angle += 360
                    else:
                        # Semi mode (-1 to 1)
                        new_angle = alpha * angle + (1 - alpha) * last_angle
                        
                    smoothed_dots.append((new_angle, new_dist, name, score))
                    self.dot_history[name] = {'angle': new_angle, 'dist': new_dist}
                else:
                    smoothed_dots.append((angle, dist, name, score))
                    self.dot_history[name] = {'angle': angle, 'dist': dist}
            
            # Clean up history
            self.dot_history = {n: d for n, d in self.dot_history.items() if n in current_names}
            
            radar_dots = smoothed_dots

            # --- Debug Info ---
            debug_info = ""
            if cfg["show_debug"]:
                device_name = "GPU" if self.classifier.device == 0 else "CPU"
                avg_latency = (total_latency / channels) if channels > 0 else 0
                debug_info = f"Device: {device_name} | Channels: {channels} | Latency: {avg_latency*1000:.1f}ms"

            if left_text or right_text or radar_dots or debug_info or channel_levels:
                self.update_signal.emit(left_text.strip(), right_text.strip(), radar_dots, debug_info, radar_mode, channel_levels)
                
            self.perf_signal.emit(total_latency)

    def stop(self):
        self.running = False

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) # Important for tray
    
    # Load Config
    current_config = config.load_config()
    
    # Windows
    settings_window = SettingsWindow(current_config)
    overlay_window = OverlayWindow()
    
    settings_window.show()
    overlay_window.show()
    overlay_window.set_radar_enabled(current_config["enable_radar"])
    
    # Worker
    worker = AudioWorker(current_config)
    
    # Connections
    worker.update_signal.connect(overlay_window.update_display)
    worker.perf_signal.connect(settings_window.update_performance)
    
    settings_window.config_updated.connect(worker.update_config)
    settings_window.config_updated.connect(lambda c: overlay_window.set_radar_enabled(c["enable_radar"]))
    settings_window.config_updated.connect(lambda c: overlay_window.update_layout_params(c.get("radar_position", "Bottom Center"), c.get("radar_size", 300)))
    
    # Initial layout update
    overlay_window.update_layout_params(current_config.get("radar_position", "Bottom Center"), current_config.get("radar_size", 300))

    settings_window.close_app.connect(worker.stop)
    settings_window.close_app.connect(app.quit)
    
    # Thread
    thread = threading.Thread(target=worker.run)
    thread.daemon = True
    thread.start()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
