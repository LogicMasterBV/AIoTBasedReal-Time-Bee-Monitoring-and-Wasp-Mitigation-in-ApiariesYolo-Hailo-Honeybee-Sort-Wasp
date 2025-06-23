This project presents a real-time, AI-driven system designed to autonomously detect and deter wasps in proximity to beehives using embedded edge computing. The system leverages a Raspberry Pi 5 in conjunction with a Hailo-8 AI accelerator (26 TOPS) to deploy a custom-trained YOLOv11n object detection model. It is capable of distinguishing between bees and wasps with high precision, ensuring that deterrent actions are species-specific and non-invasive.

The architecture integrates computer vision, object tracking, and actuation logic through a dual-axis servo turret equipped with a Class 3B laser module. Target selection is governed by a lock-on mechanism requiring a wasp to remain within a defined spatial zone for a continuous 0.5-second duration before laser activation. Tracking is handled via a lightweight implementation of the SORT algorithm, and actuation is managed using a PCA9685 PWM driver and IRLZ44N MOSFET for laser control.

The system was developed in Python and tested under constrained embedded conditions, demonstrating reliable detection performance (~60 FPS), mechanical stability, and species-selective targeting. This work contributes to the development of precision ecological protection tools and highlights the feasibility of deploying advanced AI models on low-power embedded platforms for environmental applications.
Deployment Instructions
This section provides a structured, step-by-step guide for replicating the full pipeline of this AI-powered ecological deterrence system—from dataset preparation and training to model deployment on the Raspberry Pi 5 with the Hailo+ AI accelerator.

[![Project Demo Video](https://img.youtube.com/vi/0qj1TTMSMAY/0.jpg)](https://www.youtube.com/watch?v=0qj1TTMSMAY)

## 🧪 Deployment Instructions

This section provides a structured, step-by-step guide for replicating the full pipeline of this AI-powered ecological deterrence system—from dataset preparation and training to model deployment on the Raspberry Pi 5 with the Hailo+ AI accelerator.

---

### 1. 📁 Dataset Preparation and Annotation

1. **Install Label Studio**:
   ```bash
   pip install label-studio
   label-studio start
   ```

2. **Configure Project**:
   - Create a new object detection project.
   - Add class labels: `bee`, `wasp`.
   - Upload high-resolution images (e.g., from Shutterstock).
   - Annotate objects using bounding boxes.
   - Export labels in YOLO format.

3. **Split Dataset**:
   - Organize into `images/train`, `images/val`, `labels/train`, and `labels/val`.

---

### 2. 🧠 Model Training (YOLOv11n with Ultralytics on CUDA GPU)

1. **Install Dependencies in PyCharm Terminal**:
   ```bash
   pip install ultralytics torch torchvision opencv-python matplotlib numpy pyyaml
   ```

2. **Train YOLOv11n Model**:
   ```bash
   yolo task=detect mode=train model=yolo11n.pt data=dataset_custom.yaml epochs=100 imgsz=640 batch=8 device=0
   ```

3. **Validate & Export Model**:
   - Outputs: `yolov11_custom.pt`, `yolov11_custom.onnx`

---

### 3. 🔁 Model Conversion (ONNX → HEF via Hailo SDK on WSL2)

> _Note: Hailo SDK must run on x86_64 Linux._

1. **Install WSL2 (Ubuntu 24.04)**:
   ```powershell
   wsl --install -d Ubuntu-24.04
   ```

2. **Set Up Python 3.10 Environment**:
   ```bash
   sudo add-apt-repository ppa:deadsnakes/ppa
   sudo apt update
   sudo apt install python3.10 python3.10-venv python3.10-dev
   python3.10 -m venv venv_hailo
   source venv_hailo/bin/activate
   ```

3. **Install System Dependencies**:
   ```bash
   sudo apt install build-essential python3-dev graphviz graphviz-dev python3-tk
   pip install pygraphviz scipy==1.9.3
   ```

4. **Install Hailo Dataflow Compiler**:
   ```bash
   pip install whl/hailo_dataflow_compiler-<version>.whl
   hailo -h
   ```

5. **Run Hailo Conversion Steps**:
   - Place the dataset and `yolov11_custom.onnx` in the designated folders.
   - Parse, optimize, and compile the model:
     ```bash
     python steps/3_process/parse_yolo11n.py
     python steps/3_process/optimize_yolo11n.py
     python steps/3_process/compile_yolo11n.py
     ```
   - Output: `best.hef`

---

### 4. 🔧 Hardware Setup (Prototype v2)

Components:
- Raspberry Pi 5 + AI HAT+ (Hailo-8L, 26 TOPS)
- PiCamera v3
- PCA9685 PWM Driver
- 2x MG996R Servos (Pan/Tilt)
- Class 3B Laser (<250mW)
- IRLZ44N MOSFET
- 5V 5A Power Supply

> **Important GPIO Pins**:
- I2C: SDA (Pin 3), SCL (Pin 5)
- Power: 5V (Pin 2), GND (Pin 9)

Servo channels:
- Tilt → PCA9685 Channel 0  
- Pan → PCA9685 Channel 1  
- Laser PWM → Channel 2

---

### 5. 🚀 Deploying on Raspberry Pi 5

1. **Install OS and Update Firmware**:
   ```bash
   sudo apt update && sudo apt full-upgrade
   sudo rpi-eeprom-update -a
   ```

2. **Set PCIe to Gen 3**:
   ```bash
   sudo raspi-config
   # Advanced Options > PCIe Speed > Yes > Reboot
   ```

3. **Install Hailo Software**:
   ```bash
   sudo apt install hailo-all
   hailortcli fw-control identify
   ```

4. **Install Picamera2-Compatible OpenCV**:
   ```bash
   pip install opencv-python-headless --break-system-packages
   ```

5. **Run Real-Time Detection**:
   ```bash
   python steps/2_test/detect_picamera2.py
   ```

---

### 6. 📁 Recommended Directory Structure

```
📦 Hailo8/
├── config/
│   ├── dataset_custom.yaml
│   └── yolov11n_nms_config.json
├── datasets/
│   ├── images/train, val/
│   └── labels/train, val/
├── model/
│   └── yolov11_custom.onnx
├── steps/
│   └── Conversion + Testing Scripts
├── whl/
│   └── Hailo SDK wheel files
├── best.hef
├── yolov11_custom.onnx
```
