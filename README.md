# Jetson Data Collector Pro

A PyQt5-based GUI application designed for collecting high-quality image datasets using the IMX219 camera on NVIDIA Jetson devices (Nano, Xavier NX, Orin, etc.). It provides granular control over the Image Signal Processor (ISP) settings and efficient Region of Interest (ROI) cropping.

## Features

*   **Live Preview**: Real-time video feed from the camera via GStreamer.
*   **ISP Controls**:
    *   Auto Exposure & White Balance Locks.
    *   Manual adjustments for Exposure Compensation, Gain, and Saturation.
    *   Selectable modes for White Balance, Temporal Noise Reduction (TNR), and Edge Enhancement.
    *   Adjustable strengths for TNR and Edge Enhancement.
*   **Image Manipulation**: Horizontal and Vertical flip controls.
*   **ROI Selection**:
    *   Interactive mouse-based selection.
    *   Enforced square aspect ratio for AI model compatibility.
    *   Pre-defined fixed sizes (224x224, 448x448, 896x896).
*   **Data Management**:
    *   Customizable save directory.
    *   Automatic filename incrementing.
    *   Optional filename prefixes.
    *   Support for multiple formats: PNG (default), JPG, TIFF, BMP.
*   **Cross-Platform Fallback**: Includes a "Dummy Mode" for testing the GUI on non-Jetson systems (macOS/Windows) without a CSI camera.

## Prerequisites

*   **Hardware**: NVIDIA Jetson device with an IMX219 camera (e.g., Raspberry Pi Camera Module V2).
*   **OS**: Linux (JetPack) for full functionality. macOS/Windows for UI testing only.
*   **Python**: 3.6+

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd data_collect_gui
    ```

2.  **Install dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    pip install -r requirements.txt
    ```

    **Hardware-Specific Instructions:**
    *   **macOS**: The app is tested and works on macOS. Ensure `opencv-python` is installed.
    *   **NVIDIA Jetson**: The app is tested on Jetson. Use the pre-installed OpenCV (with GStreamer support) provided by JetPack. **Do not** install `opencv-python` via pip, as it often lacks GStreamer support. If missing, install via apt: `sudo apt-get install python3-opencv`.

## Usage

1.  **Run the application:**
    ```bash
    python3 main.py
    ```

2.  **Controls:**
    *   **Left Panel**: Adjust camera ISP settings (Gain, Exposure, etc.). Changes apply immediately (triggering a pipeline restart).
    *   **Center**: View the live feed. Click and drag to draw a square ROI.
    *   **Right Panel**:
        *   Select save directory.
        *   Set filename prefix and format.
        *   Choose a fixed ROI size or reset selection.
        *   Click **CAPTURE FRAME** to save the image (cropped to ROI if selected).

## Configuration

Default settings (resolution, framerate, exposure limits) can be modified in `config.json`.

## Project Structure

```
.
├── main.py                 # Application entry point
├── config.json             # Configuration file
├── requirements.txt        # Python dependencies
└── src/
    ├── config.py           # Config loading logic
    ├── core/
    │   └── video_thread.py # GStreamer pipeline & video capture
    └── ui/
        ├── main_window.py  # Main GUI window & logic
        └── widgets.py      # Custom UI widgets (VideoLabel)
```
