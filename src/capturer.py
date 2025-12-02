import soundcard as sc
import numpy as np
import scipy.signal

class AudioCapturer:
    def __init__(self, sample_rate=16000, chunk_duration=1.0):
        self.target_sr = sample_rate
        self.chunk_duration = chunk_duration
        
        # Find the loopback microphone corresponding to the default speaker
        default_speaker = sc.default_speaker()
        print(f"Default Speaker: {default_speaker.name}")
        
        # Search for loopback device
        loopback_mic = None
        try:
            mics = sc.all_microphones(include_loopback=True)
            for mic in mics:
                if mic.name == default_speaker.name:
                    loopback_mic = mic
                    break
            
            # Fallback: if exact name match fails, try to find one that looks like a loopback of it
            if loopback_mic is None:
                print("Warning: Exact loopback device match not found. Trying to find by partial name...")
                for mic in mics:
                    if default_speaker.name in mic.name:
                        loopback_mic = mic
                        break
        except Exception as e:
            print(f"Error listing microphones: {e}")

        if loopback_mic:
            self.mic = loopback_mic
            print(f"Using Loopback Device: {self.mic.name}")
        else:
            print("Error: Could not find loopback device for default speaker.")
            # Fallback to default microphone if loopback fails (not ideal but prevents crash)
            self.mic = sc.default_microphone()
            print(f"Fallback to Default Microphone: {self.mic.name}")

    def capture_loop(self):
        # Determine native sample rate? Soundcard doesn't always tell us easily before opening.
        # We'll just record a chunk and see.
        # Actually, sc.default_speaker().record(samplerate=...) might work if supported.
        # But usually loopback is fixed to system rate.
        
        # Let's try to record with a standard rate, soundcard handles resampling often?
        # No, soundcard usually records at system rate.
        
        # We will record chunks of 'chunk_duration' seconds.
        # We need to know the system sample rate to ask for the right number of frames.
        # soundcard doesn't expose system rate easily. We can guess 44100 or 48000.
        # Or we can just ask for a large number of frames and measure time?
        # Better: use a fixed rate for recording if possible.
        
        record_sr = 44100 # Common default
        num_frames = int(record_sr * self.chunk_duration)
        
        with self.mic.recorder(samplerate=record_sr) as recorder:
            while True:
                data = recorder.record(numframes=num_frames)
                # data is [frames, channels]
                
                # Resample to target_sr (16000)
                if record_sr != self.target_sr:
                    # Calculate new number of samples
                    new_samples = int(len(data) * self.target_sr / record_sr)
                    data = scipy.signal.resample(data, new_samples)
                
                yield data
