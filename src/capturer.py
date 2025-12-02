import soundcard as sc
import numpy as np
import scipy.signal
import warnings

# Suppress soundcard data discontinuity warning
try:
    from soundcard.mediafoundation import SoundcardRuntimeWarning
    warnings.filterwarnings("ignore", category=SoundcardRuntimeWarning)
except ImportError:
    # Fallback if specific warning class is not available or path is different
    warnings.filterwarnings("ignore", message="data discontinuity in recording")

class AudioCapturer:
    @staticmethod
    def get_devices():
        try:
            return [m.name for m in sc.all_microphones(include_loopback=True)]
        except Exception as e:
            print(f"Error listing devices: {e}")
            return []

    def __init__(self, sample_rate=16000, chunk_duration=1.0, device_name=None):
        self.target_sr = sample_rate
        self.chunk_duration = chunk_duration
        self.device_name = device_name
        self.mic = None
        self._init_mic()

    def _init_mic(self):
        self.mic = None
        if self.device_name:
            try:
                mics = sc.all_microphones(include_loopback=True)
                for mic in mics:
                    if mic.name == self.device_name:
                        self.mic = mic
                        break
            except Exception as e:
                print(f"Error finding device '{self.device_name}': {e}")
        
        if self.mic is None:
            try:
                default_speaker = sc.default_speaker()
                print(f"Default Speaker: {default_speaker.name}")
                
                loopback_mic = None
                mics = sc.all_microphones(include_loopback=True)
                for mic in mics:
                    if mic.name == default_speaker.name:
                        loopback_mic = mic
                        break
                
                if loopback_mic is None:
                    print("Warning: Exact loopback device match not found. Trying to find by partial name...")
                    for mic in mics:
                        if default_speaker.name in mic.name:
                            loopback_mic = mic
                            break
                
                if loopback_mic:
                    self.mic = loopback_mic
            except Exception as e:
                print(f"Error finding loopback device: {e}")

        if self.mic is None:
            print("Error: Could not find loopback device for default speaker.")
            try:
                self.mic = sc.default_microphone()
            except Exception as e:
                print(f"Error getting default microphone: {e}")

        if self.mic:
            print(f"Using Audio Device: {self.mic.name}")
        else:
            print("Error: No audio device found.")

    def capture_loop(self):
        record_sr = 44100
        import time
        
        while True:
            try:
                if self.mic is None:
                    self._init_mic()
                    if self.mic is None:
                        print("No microphone available. Retrying in 2s...")
                        time.sleep(2)
                        continue

                print(f"Starting recording on {self.mic.name}...")
                with self.mic.recorder(samplerate=record_sr) as recorder:
                    while True:
                        num_frames = int(record_sr * self.chunk_duration)
                        data = recorder.record(numframes=num_frames)
                        
                        if record_sr != self.target_sr:
                            new_samples = int(len(data) * self.target_sr / record_sr)
                            data = scipy.signal.resample(data, new_samples)
                        
                        yield data
            except RuntimeError as e:
                print(f"Audio Runtime Error: {e}")
                if "0x88890004" in str(e) or "0x100000001" in str(e):
                     print("Device invalidated. Reconnecting...")
                     time.sleep(1)
                     self._init_mic()
                else:
                     print("Unknown audio error. Retrying...")
                     time.sleep(1)
            except Exception as e:
                print(f"Unexpected error: {e}")
                time.sleep(1)
