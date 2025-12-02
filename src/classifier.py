import numpy as np
from transformers import pipeline
import torch
import time
import os

class AudioClassifier:
    def __init__(self, use_gpu=False):
        self.device = 0 if (use_gpu and torch.cuda.is_available()) else -1
        print(f"Initializing Classifier on device: {'GPU' if self.device == 0 else 'CPU'}")
        
        print("Loading Audio Spectrogram Transformer (AST) model...")
        
        # Check for local model
        local_model_path = os.path.join("models", "ast-finetuned-audioset-10-10-0.4593")
        model_source = "mit/ast-finetuned-audioset-10-10-0.4593"
        
        if os.path.exists(local_model_path):
            print(f"Found local model at: {local_model_path}")
            model_source = local_model_path
        else:
            print(f"Local model not found. Downloading/Using cache from Hugging Face: {model_source}")

        try:
            self.pipe = pipeline("audio-classification", model=model_source, device=self.device)
            print("Model loaded.")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.pipe = None

    def set_device(self, use_gpu):
        new_device = 0 if (use_gpu and torch.cuda.is_available()) else -1
        if new_device != self.device:
            print(f"Switching device to {'GPU' if new_device == 0 else 'CPU'}...")
            self.device = new_device
            
            # Re-determine model source
            local_model_path = os.path.join("models", "ast-finetuned-audioset-10-10-0.4593")
            model_source = local_model_path if os.path.exists(local_model_path) else "mit/ast-finetuned-audioset-10-10-0.4593"

            # Reload pipeline to switch device reliably
            try:
                self.pipe = pipeline("audio-classification", model=model_source, device=self.device)
            except Exception as e:
                print(f"Error switching device: {e}")

    def predict(self, waveform, top_k=5):
        if self.pipe is None:
            return [], 0.0

        # Ensure waveform is float32
        if waveform.dtype != np.float32:
            waveform = waveform.astype(np.float32)

        start_time = time.time()
        try:
            predictions = self.pipe(waveform, top_k=top_k)
        except Exception as e:
            print(f"Prediction error: {e}")
            return [], 0.0
        end_time = time.time()
        latency = end_time - start_time
        
        results = []
        for p in predictions:
            results.append((p['label'], p['score']))
            
        return results, latency

