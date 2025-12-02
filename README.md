# AI Sound Assistant for the Deaf / 聋人 AI 声音辅助工具

[English](#english) | [中文](#chinese)

<a name="english"></a>
## English

This tool captures system audio, classifies it using AI (Audio Spectrogram Transformer), and displays the detected sounds on a transparent overlay or a radar view.

### Features
- **GUI Launcher**: User-friendly interface to configure settings.
- **System Tray Support**: Minimize the tool to the system tray.
- **Real-time Audio Capture**: Captures system loopback audio.
- **AI Classification**: Uses Hugging Face's AST model (PyTorch) to identify 527 types of sounds.
- **Hardware Acceleration**: Switch between CPU and GPU for inference.
- **Visualizations**:
  - **Directional Text**: Shows sounds on Left/Right.
  - **Radar View**: Visualizes sound position and type on a radar.
  - **Channel Levels**: Visualizes the loudness of each audio channel around the radar.
- **Customization**:
  - **Time Slice**: Adjust analysis window duration.
  - **Top-K**: Control how many sound types to display.
  - **Thresholds**: Adjust confidence thresholds.
  - **Normalization**: Toggle input normalization with a silence threshold.
- **Performance Monitor**: Real-time display of model inference latency.
- **Configuration**: Auto-save and load settings.

### Setup
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Ensure you have Microsoft Visual C++ Redistributable installed.*

2. **Download Model (Optional but Recommended)**:
   If you have connection issues with Hugging Face, or want to run offline:
   ```bash
   python src/download_model.py
   ```
   This will download the model to the `models/` directory.

3. **Run**:
   ```bash
   python src/main.py
   ```

---

<a name="chinese"></a>
## 中文

这是一个基于人工智能的听障辅助工具，能够捕获系统音频，使用 AI 模型（AST）进行分类，并通过透明覆盖层或雷达视图显示检测到的声音。

### 功能特性
- **图形界面启动器**：提供友好的配置界面。
- **托盘化支持**：支持最小化到系统托盘运行。
- **实时音频捕获**：捕获系统内部录音（Loopback）。
- **AI 识别**：使用 Hugging Face 的 AST 模型（PyTorch）识别 527 种声音。
- **硬件加速**：支持在 CPU 和 GPU 之间切换模型运行。
- **可视化展示**：
  - **方向文字**：在屏幕左右显示声音类型。
  - **雷达视图**：在雷达上通过点的位置展示声源方向和类型。
  - **声道音量**：在雷达周围显示每个声道的实时音量。
- **自定义设置**：
  - **时间片**：调节分析的时间窗口大小。
  - **Top-K**：控制显示多少种最显著的声音。
  - **阈值**：调节置信度阈值。
  - **标准化**：开关输入声音标准化，并提供静音阈值调节。
- **性能监控**：实时显示模型推理延迟。
- **配置管理**：自动保存和读取配置文件。

### 安装与运行
1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```
   *注意：请确保已安装 Microsoft Visual C++ Redistributable。*

2. **下载模型（可选但推荐）**：
   如果连接 Hugging Face 遇到网络问题，或希望离线运行：
   ```bash
   python src/download_model.py
   ```
   这将把模型下载到 `models/` 目录。

3. **运行**：
   ```bash
   python src/main.py
   ```

### 注意事项
CPU模式请把Time Slice设置在1.0秒或更高（取决于您的CPU性能）
GPU模式需要安装CUDA，Time Slice设置请参考屏幕上方（需要开启Show Debug Info）的Latency，如果小于100ms，可随意（会占用GPU性能）。

安装VB-CABLE可以激活全向雷达，但是需要游戏支持多声道（>2）输出，需自行设置。

由Copilot协助开发。