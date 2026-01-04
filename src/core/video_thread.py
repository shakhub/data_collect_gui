import time

import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

from src.config import (
    CAM_CONF,
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
)


class VideoThread(QThread):
    """Thread for capturing video from the camera."""

    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        """Initialize the video thread."""
        super().__init__()
        self._run_flag = True
        self.exposure_range = None
        self.gain_range = None
        self.ae_lock = False
        self.awb_lock = False
        self.saturation = 1.0
        self.wb_mode = 1  # auto
        self.tnr_mode = 1  # fast
        self.tnr_strength = 0.5
        self.ee_mode = 1  # fast
        self.ee_strength = 0.5
        self.h_flip = False
        self.v_flip = False
        self.cap = None

    def build_pipeline(self):
        """Build the GStreamer pipeline string."""
        pipeline = "nvarguscamerasrc "
        if self.exposure_range:
            pipeline += (
                f'exposuretimerange="{self.exposure_range[0]} '
                f'{self.exposure_range[1]}" '
            )
        if self.gain_range:
            pipeline += (
                f'gainrange="{self.gain_range[0]} {self.gain_range[1]}" '
            )
        if self.ae_lock:
            pipeline += "aelock=true "
        if self.awb_lock:
            pipeline += "awblock=true "

        pipeline += (
            f"saturation={self.saturation} "
            f"wbmode={self.wb_mode} "
            f"tnr-mode={self.tnr_mode} "
            f"tnr-strength={self.tnr_strength} "
            f"ee-mode={self.ee_mode} "
            f"ee-strength={self.ee_strength} "
        )

        pipeline += (
            f"! video/x-raw(memory:NVMM), width={DEFAULT_WIDTH}, "
            f"height={DEFAULT_HEIGHT}, format=NV12, "
            f"framerate={CAM_CONF['framerate']} ! "
            f"nvvidconv flip-method={self.get_flip_method()} ! "
            f"video/x-raw, width={DISPLAY_WIDTH}, "
            f"height={DISPLAY_HEIGHT}, format=BGRx ! "
            f"videoconvert ! video/x-raw, format=BGR ! appsink drop=1"
        )
        return pipeline

    def get_flip_method(self):
        """
        Calculate flip-method for nvvidconv.
        0: identity
        1: counterclockwise
        2: rotate-180
        3: clockwise
        4: horizontal-flip
        5: upper-right-diagonal
        6: vertical-flip
        7: upper-left-diagonal
        
        We only care about H and V flips combined with 0 rotation.
        H=False, V=False -> 0
        H=True,  V=False -> 4
        H=False, V=True  -> 6
        H=True,  V=True  -> 2 (rotate-180 is equivalent to H+V flip)
        """
        if self.h_flip and self.v_flip:
            return 2
        elif self.h_flip:
            return 4
        elif self.v_flip:
            return 6
        return 0

    def run(self):
        """Run the video capture loop."""
        gst_str = self.build_pipeline()
        self.cap = cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)

        # Fallback for non-Jetson environments (e.g., macOS/Windows)
        if not self.cap.isOpened():
            print("GStreamer pipeline failed. Trying default webcam...")
            self.cap = cv2.VideoCapture(0)

        # If still not opened, we will generate dummy frames in the loop
        using_dummy = not (self.cap and self.cap.isOpened())
        if using_dummy:
            print("Camera not found. Using dummy frame generator.")

        while self._run_flag:
            if not using_dummy:
                ret, frame = self.cap.read()
                if ret:
                    # Resize to match expected display size if needed,
                    # or just let the GUI handle the frame size.
                    # For consistency with the pipeline, we might want to resize
                    # but the GUI adapts to the frame size.
                    self.change_pixmap_signal.emit(frame)
                else:
                    time.sleep(0.1)
            else:
                # Generate dummy noise frame
                frame = np.random.randint(
                    0, 256, (DISPLAY_HEIGHT, DISPLAY_WIDTH, 3), dtype=np.uint8
                )
                cv2.putText(
                    frame,
                    "NO CAMERA - DUMMY MODE",
                    (50, 270),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 255, 255),
                    2,
                )
                self.change_pixmap_signal.emit(frame)
                time.sleep(0.1)

        if self.cap:
            self.cap.release()

    def stop(self):
        """Stop the video capture thread."""
        self._run_flag = False
        self.wait()

    def update_settings(
        self,
        exposure,
        gain,
        ae_lock,
        awb_lock,
        saturation,
        wb_mode,
        tnr_mode,
        tnr_strength,
        ee_mode,
        ee_strength,
        h_flip,
        v_flip,
    ):
        """Update camera settings and restart the pipeline."""
        self._run_flag = False
        self.wait()
        self.exposure_range = exposure
        self.gain_range = gain
        self.ae_lock = ae_lock
        self.awb_lock = awb_lock
        self.saturation = saturation
        self.wb_mode = wb_mode
        self.tnr_mode = tnr_mode
        self.tnr_strength = tnr_strength
        self.ee_mode = ee_mode
        self.ee_strength = ee_strength
        self.h_flip = h_flip
        self.v_flip = v_flip
        self._run_flag = True
        self.start()
