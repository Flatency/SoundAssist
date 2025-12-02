# AI Sound Assistant for the Deaf

This tool captures system audio, classifies it using AI (Audio Spectrogram Transformer), and displays the detected sounds on a transparent overlay, similar to Minecraft's subtitles.

## Features
- **Real-time Audio Capture**: Uses `soundcard` to capture system loopback audio.
- **AI Classification**: Uses Hugging Face's AST model (PyTorch) to identify 527 types of sounds.
- **Directional Indicator**: Shows sounds on the Left or Right side of the screen based on stereo channel intensity.
- **Transparent Overlay**: A click-through overlay that sits on top of other windows (e.g., games, videos).

## Setup

1. **Install Dependencies**:
   The environment should already be set up. If not:
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   .\venv\Scripts\python src/main.py
   ```
   Or simply run the `run.bat` script.

## Notes
- **First Run**: The application will download the YAMNet model (approx. a few MBs) and the class map CSV file. This requires an internet connection.
- **Audio Device**: The tool attempts to use the default system loopback device. Ensure your system audio is playing through the default speakers.
- **Performance**: The AI model runs on CPU by default. It processes audio in ~1-second chunks.
- **Overlay**: The overlay is transparent. If you don't see it, try playing some distinct sounds (clapping, dog barking, music) to trigger the display.

## Troubleshooting
- If `soundcard` fails to find a loopback device, ensure you are on Windows and have a valid output device active.
- If the overlay is black instead of transparent, your system might not support the specific transparency method used.
