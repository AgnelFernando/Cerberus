# Cerberus: Autonomous Robot Dog Surveillance System

Welcome to **Cerberus**, an AI-powered surveillance system built on the Unitree Go1 robot dog. The project performs **localization and mapping** using ultrasonic sensors, and leverages the **fisheye camera** for **object detection** and **person activity recognition**.

---

## Table of Contents

* [Introduction](#introduction)
* [Robot Architecture](#robot-architecture)
* [System Overview](#system-overview)
* [Software Flow](#software-flow)
* [Setup Instructions](#setup-instructions)
* [Running the Patrol Service](#running-the-patrol-service)
* [Acknowledgements](#acknowledgements)

---

## Introduction

The goal of this project is to develop an **intelligent, autonomous surveillance robot dog** capable of patrolling, detecting people and their activities, and reporting to a connected monitoring system.

---

## Robot Architecture

![image](https://github.com/user-attachments/assets/8ed19ad7-aa7a-4b97-8f6f-a3a39f790e90)

The **Unitree Go1 EDU** system has the following architecture:

* **Main Control Board**: MCU (`192.168.123.10`)
* **Motion Control Board**: Raspberry Pi 4B (`192.168.123.161`)
* **Sensing Motherboards**:

  * Nano (head) → `192.168.123.13`
  * Nano (body) → `192.168.123.14`
  * Nano or NX (body) → `192.168.123.15`

For this project, I used:

* The **Motion Control Board** for processing and robot commands
* The **Sensing Motherboard (Head)** for camera-based perception

You can connect to the Motion Control Board via **Wi-Fi** or **Ethernet**. Once inside (via SSH), you can access all other internal nodes.

---

## System Overview

* **Camera Feed**: Fisheye camera data is received via **UDP** from the head board.
* **Ultrasonic Sensors**: A Python script on the Motion Control Board listens to **LCM** messages and retransmits them via **MQTT**.
* **Robot Control**: MQTT topics are used to publish control commands to the Go1.
* **Mapping and Navigation**: The system uses an **occupancy grid map** to autonomously patrol and avoid obstacles.

---

## Software Flow

```
              ┌────────────────────────────┐
              │   External Control System  │
              │   (your computer, IP .100) │
              └────────────┬───────────────┘
                           │ Wi-Fi (192.168.123.0/24)
              ┌────────────▼───────────────┐
              │  Motion Control Board (Pi) │
              │ - us_mqtt.py (MQTT relay)  │
              │ - patrol_service.py        │
              └────────────┬───────────────┘
                           │
              ┌────────────▼───────────────┐
              │  Sensing Board (Head)      │
              │ - UDP camera streaming     │
              └────────────────────────────┘
```

* `patrol_service.py` subscribes to MQTT topics like `robot/ultrasonic` and launches the `object_detector` module.
* `object_detector` receives UDP video, processes the frames with OpenCV (GStreamer enabled), and displays the stream.
* The robot's movement is coordinated using local sensor data and a live occupancy grid map.

---

## Setup Instructions

### 1. Clone Repositories

```bash
git clone https://github.com/AgnelFernando/Cerberus.git
git clone https://github.com/unitreerobotics/UnitreecameraSDK.git
```

### 2. Connect to Go1's Wi-Fi

* Wi-Fi Name: `GoXXXXXXXX`
* Password: `0000000`

### 3. Transfer Files to Motion Control Board (Pi)

```bash
scp -r UnitreeCameraSDK pi@192.168.12.1:/home/pi/
scp -r Cerberus/us_lcm pi@192.168.12.1:/home/pi/
scp Cerberus/scripts/kill_cam_process.sh pi@192.168.12.1:/home/pi/
# password: 123
```

### 4. Transfer Files to Sensing Board (Head)

```bash
ssh pi@192.168.12.1
scp -r UnitreeCameraSDK unitree@192.168.123.13:/home/unitree/
scp kill_cam_process.sh unitree@192.168.123.13:/home/unitree/
# password: 123
```

### 5. Configure Camera Transmission

```bash
ssh unitree@192.168.123.13
chmod +x kill_cam_process.sh
./kill_cam_process.sh
cd UnitreeCameraSDK
vim trans_rect_config.yaml
```

Modify the `IpLastSegment` field:

```yaml
data: [ 15. ]   # Change this
# to:
data: [ 100. ]  # So that it streams to your computer at .100
```

Then build and launch the camera stream:

```bash
mkdir build
cd build
cmake ..
make
cd ..
./bin/example_putImagetrans
```

Leave this terminal open to maintain the stream.

---

## Running the Patrol Service

### 1. On the Motion Control Board

```bash
ssh pi@192.168.12.1
cd us_lcm
python us_mqtt.py
```

### 2. On Your Local System

```bash
cd Cerberus
conda create -n cerberus python=3.10
conda activate cerberus
pip install -r requirements.txt
```

### 3. Install OpenCV with GStreamer Support

```bash
git clone https://github.com/opencv/opencv.git
cd opencv
mkdir build && cd build

cmake -D CMAKE_BUILD_TYPE=Release \
      -D CMAKE_INSTALL_PREFIX=$CONDA_PREFIX \
      -D PYTHON_EXECUTABLE=$(which python) \
      -D WITH_GSTREAMER=ON \
      -D BUILD_opencv_python3=ON \
      -D OPENCV_GENERATE_PKGCONFIG=ON \
      ..

make -j$(nproc)
make install
```

### 4. Run the Patrol Service

Ensure Go1 is in walk mode, then:

```bash
python patrol_service.py
```

This will:

* Start receiving ultrasonic data from MQTT
* Launch the object detection module
* Begin autonomous patrol based on a grid map

---

## Contributions

Contributions are welcome!

If you’d like to improve Cerberus, feel free to:

1. Fork the repo
2. Create a feature branch
3. Submit a pull request

---

## Acknowledgements

* 📚 [Unitree Docs](https://unitree-docs.readthedocs.io/en/latest/get_started/Go1_Edu.html)
* 🐾 [go1pylib by chinmaynehate](https://github.com/chinmaynehate/go1pylib)
* 🔧 [UnitreeCameraSDK by YushuTech](https://github.com/unitreerobotics/UnitreecameraSDK)

