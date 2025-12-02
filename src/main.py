import sys
import threading
import numpy as np
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal

from classifier import AudioClassifier
from capturer import AudioCapturer
from overlay import OverlayWindow

class AudioWorker(QObject):
    update_signal = pyqtSignal(str, str) # left_text, right_text

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        print("Initializing Audio Capturer...")
        capturer = AudioCapturer()
        
        print("Initializing Classifier...")
        classifier = AudioClassifier()
        
        print("Starting Audio Loop...")
        for audio_chunk in capturer.capture_loop():
            if not self.running:
                break
            
            # audio_chunk: [frames, channels]
            # Check for silence
            rms = np.sqrt(np.mean(audio_chunk**2))
            if rms < 0.01: # Silence threshold
                continue
                
            channels = audio_chunk.shape[1]
            left_text = ""
            right_text = ""
            
            # Process Left Channel
            if channels >= 1:
                left_audio = audio_chunk[:, 0]
                # Normalize? YAMNet expects [-1, 1]. It is already float.
                results = classifier.predict(left_audio)
                # Filter results
                valid_results = [f"{name} ({score:.2f})" for name, score in results if score > 0.2 and name != 'Silence']
                if valid_results:
                    left_text = "< " + "\n< ".join(valid_results)
            
            # Process Right Channel
            if channels >= 2:
                right_audio = audio_chunk[:, 1]
                results = classifier.predict(right_audio)
                valid_results = [f"{name} ({score:.2f})" for name, score in results if score > 0.2 and name != 'Silence']
                if valid_results:
                    right_text = "\n".join(valid_results) + " >"
            
            if left_text or right_text:
                self.update_signal.emit(left_text, right_text)

    def stop(self):
        self.running = False

def main():
    app = QApplication(sys.argv)
    
    window = OverlayWindow()
    window.show()
    
    worker = AudioWorker()
    worker.update_signal.connect(window.update_display)
    
    thread = threading.Thread(target=worker.run)
    thread.daemon = True
    thread.start()
    
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        worker.stop()

if __name__ == "__main__":
    main()
