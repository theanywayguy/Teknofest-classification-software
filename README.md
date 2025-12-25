<div align="center">

# 🚀 Aegis Turret Control System

### TEKNOFEST 2026 - Mersin University Team

**Autonomous Object Detection, Tracking & Turret Control Suite** Powered by **Ultralytics YOLOv8** + **OpenCV** + **Arduino**

</div>

---

## 📋 Overview

Aegis is the mission control software designed for our autonomous turret. It combines real-time computer vision with hardware control to handle two distinct competition scenarios: **Standard Engagement** (Friend/Foe) and the **Memory Mission** (OCR & Shape Recognition).

## ✨ Key Features

### 🎯 Main Control System (`main.py`)

- **GUI Dashboard:** Full control panel with live video feed, turret telemetry, and mode switching.
- **Standard Mode (Friend/Foe):**
  - Detects Friendly (Blue/Green) vs. Foe (Red/Pink) balloons.
  - **Auto-Lock:** Automatically selects and tracks the closest enemy.
  - **Vector Tracking:** Visualizes the turret's aim path to the target.
- **Memory Mode (Mission Logic):**
  - **OCR:** Reads platform letters (A, B, C...) to determine mission parameters.
  - **Smart Seeking:** Automatically pans to the platform angle.
  - **Shape Switching:** Swaps AI models on-the-fly to hunt specific shapes (Triangles, Squares, etc.).
- **Firing Logic:** Calculates precision and sends "Fire" commands only when the crosshair is stable on the target.

### 🛠️ Standalone Utilities

For rapid testing without running the full system:

- **`run_live_cam.py`**: Webcam test. Press **'A'** to toggle between "Balloon Model" and "Shape Model" in real-time.
- **`run_video_inference.py`**: Process recorded videos (e.g., `white-ball.mp4`) with full bounding boxes and CSV logging.
- **`test_turret_manual.py`**: Direct hardware link. Drive the turret with **WASD** to test motors and firing mechanism.

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone [https://github.com/theanywayguy/Teknofest-classification-software](https://github.com/theanywayguy/Teknofest-classification-software)
cd Teknofest-classification-software
```

### 2. Create & Activate Environment(HIGHLY RECOMMENDED)

```bash
conda create -n teknofest python=3.12
conda activate teknofest
```

### 3. Install Dependencies

GPU (if available for better performance)

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install ultralytics opencv-python deep-sort-realtime numpy pandas matplotlib scipy psutil pyyaml tqdm pandas
```

CPU Only

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install ultralytics opencv-python deep-sort-realtime numpy pandas matplotlib scipy psutil pyyaml tqdm pandas
```

### 4. Usage

```bash
conda activate teknofest
cd Aegis-Software-Stable
python main.py
```

## 📂 Project Structure

- **`main.py`**: Entry point for the Aegis GUI application.
- **`mission_control.py`**: The "Brain". Manages state machines and coordinates vision/turret.
- **`modes.py`**: The Logic. Contains specific behavior for Standard and Memory missions.
- **`vision.py`**: The Eyes. Wrapper for YOLOv8 inference and OCR functions.
- **`turret.py`**: The Muscles. Handles Serial communication with STM32.
- **`config.py`**: Central settings (Thresholds, Colors etc...).
- **`ui.py`**: Tkinter GUI layout design.

<div align="center"> Developed for Teknofest 2026 </div>
