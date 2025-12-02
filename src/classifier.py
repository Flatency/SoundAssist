import numpy as np
from transformers import pipeline
import torch

class AudioClassifier:
    def __init__(self):
        print("Loading Audio Spectrogram Transformer (AST) model...")
        # Use a standard model trained on AudioSet
        # This might download ~300MB on first run
        device = 0 if torch.cuda.is_available() else -1
        self.pipe = pipeline("audio-classification", model="mit/ast-finetuned-audioset-10-10-0.4593", device=device)
        print("Model loaded.")

    def predict(self, waveform):
        # waveform: 1D numpy array of float32, sample rate 16000
        # The pipeline expects a numpy array. It assumes 16kHz usually for this model.
        
        # Ensure waveform is float32
        if waveform.dtype != np.float32:
            waveform = waveform.astype(np.float32)

        # Run prediction
        # top_k=5 to get top 5 results
        # We pass the raw waveform. The pipeline handles it.
        # Note: For optimal results, ensure the input is 16kHz.
        try:
            predictions = self.pipe(waveform, top_k=5)
        except Exception as e:
            print(f"Prediction error: {e}")
            return []
        
        # predictions is a list of dicts: [{'score': 0.9, 'label': 'Speech'}, ...]
        results = []
        for p in predictions:
            results.append((p['label'], p['score']))
            
        return results
