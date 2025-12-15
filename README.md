<div align="center">

# 🚀 TEKNOFEST Classification Software

**Real-time Object Detection & Tracking Suite**  
Powered by **Ultralytics YOLOv8** + **OpenCV** 

Tailored for Mersin University Teknofest Competition Team 

##  Features
- Friendly (Blue), Foe (Red) balloon detection
- Bounding boxes around identified targets, with their center points defined
- Outputs the foe's coordinates to a CSV file
- Gives shooting order
- video_inference.py for simple testing over recorded video
- webcam_detection.py for webcam detection testing

## 🛠 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/theanywayguy/Teknofest-classification-software
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
cd Main-Software
python main.py
```

