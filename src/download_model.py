import os
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

def download_model():
    model_id = "mit/ast-finetuned-audioset-10-10-0.4593"
    local_dir = os.path.join("models", "ast-finetuned-audioset-10-10-0.4593")
    
    print(f"Downloading model '{model_id}' to '{local_dir}'...")
    
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    
    try:
        # Download feature extractor
        print("Downloading feature extractor...")
        feature_extractor = AutoFeatureExtractor.from_pretrained(model_id)
        feature_extractor.save_pretrained(local_dir)
        
        # Download model
        print("Downloading model...")
        model = AutoModelForAudioClassification.from_pretrained(model_id)
        model.save_pretrained(local_dir)
        
        print("Download complete.")
        print(f"Model saved to: {os.path.abspath(local_dir)}")
    except Exception as e:
        print(f"Error downloading model: {e}")
        print("Please ensure you have a stable internet connection (VPN might be required).")

if __name__ == "__main__":
    download_model()
