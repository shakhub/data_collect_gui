import os

import cv2
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QKeySequence, QPixmap
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QShortcut,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from src.config import (
    APP_CONF,
    CAM_CONF,
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
)
from src.core.video_thread import VideoThread
from src.ui.widgets import VideoLabel


class DataCollectorApp(QMainWindow):
    """Main application window for data collection."""

    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.setWindowTitle(APP_CONF["window_title"])
        geom = APP_CONF["window_geometry"]
        self.setGeometry(geom[0], geom[1], geom[2], geom[3])

        self.save_dir = os.path.join(os.getcwd(), APP_CONF["save_directory"])
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        self.current_frame = None
        self.capture_count = 0

        self.init_ui()
        self.update_filename_counter()

        self.thread = VideoThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.start()
        
        # Ensure the window has focus initially so shortcuts work immediately
        self.setFocus()

    def init_ui(self):
        """Initialize the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_row = QHBoxLayout()
        central_widget.setLayout(main_row)

        # --- LEFT: Camera Settings ---
        left_panel = QVBoxLayout()
        left_panel.setSpacing(15)
        main_row.addLayout(left_panel, stretch=1)

        # 1. Camera Settings (ISP Control)
        cam_group = QGroupBox("ISP Control")
        cam_layout = QVBoxLayout()
        self.chk_ae_lock = QCheckBox("Lock Auto Exposure")
        self.chk_ae_lock.stateChanged.connect(self.trigger_restart)
        cam_layout.addWidget(self.chk_ae_lock)
        self.chk_awb_lock = QCheckBox("Lock White Balance")
        self.chk_awb_lock.stateChanged.connect(self.trigger_restart)
        cam_layout.addWidget(self.chk_awb_lock)

        # Exposure Compensation
        cam_layout.addWidget(QLabel("Exposure Compensation:"))
        exp_layout = QHBoxLayout()
        self.exp_slider = QSlider(Qt.Horizontal)
        self.exp_slider.setMinimum(1)
        self.exp_slider.setMaximum(10)
        self.exp_slider.setValue(5)
        self.exp_slider.sliderReleased.connect(self.trigger_restart)
        self.lbl_exp_val = QLabel(str(self.exp_slider.value()))
        self.exp_slider.valueChanged.connect(
            lambda v: self.lbl_exp_val.setText(str(v)))
        exp_layout.addWidget(self.exp_slider)
        exp_layout.addWidget(self.lbl_exp_val)
        cam_layout.addLayout(exp_layout)

        # Gain
        cam_layout.addWidget(QLabel("Gain:"))
        gain_layout = QHBoxLayout()
        self.gain_slider = QSlider(Qt.Horizontal)
        self.gain_slider.setMinimum(10)
        self.gain_slider.setMaximum(100)  # 1.0 to 10.0
        self.gain_slider.setValue(10)
        self.gain_slider.sliderReleased.connect(self.trigger_restart)
        self.lbl_gain_val = QLabel(str(self.gain_slider.value() / 10.0))
        self.gain_slider.valueChanged.connect(
            lambda v: self.lbl_gain_val.setText(str(v / 10.0)))
        gain_layout.addWidget(self.gain_slider)
        gain_layout.addWidget(self.lbl_gain_val)
        cam_layout.addLayout(gain_layout)

        # Saturation
        cam_layout.addWidget(QLabel("Saturation:"))
        sat_layout = QHBoxLayout()
        self.sat_slider = QSlider(Qt.Horizontal)
        self.sat_slider.setMinimum(0)
        self.sat_slider.setMaximum(20)  # 0.0 to 2.0
        self.sat_slider.setValue(10)
        self.sat_slider.sliderReleased.connect(self.trigger_restart)
        self.lbl_sat_val = QLabel(str(self.sat_slider.value() / 10.0))
        self.sat_slider.valueChanged.connect(
            lambda v: self.lbl_sat_val.setText(str(v / 10.0)))
        sat_layout.addWidget(self.sat_slider)
        sat_layout.addWidget(self.lbl_sat_val)
        cam_layout.addLayout(sat_layout)

        # White Balance Mode
        cam_layout.addWidget(QLabel("White Balance Mode:"))
        self.combo_wb = QComboBox()
        self.combo_wb.addItems(
            [
                "off",
                "auto",
                "incandescent",
                "fluorescent",
                "warm-fluorescent",
                "daylight",
                "cloudy-daylight",
                "twilight",
                "shade",
                "manual",
            ]
        )
        self.combo_wb.setCurrentIndex(1)  # auto
        self.combo_wb.currentIndexChanged.connect(self.trigger_restart)
        cam_layout.addWidget(self.combo_wb)

        # TNR Mode
        cam_layout.addWidget(QLabel("TNR Mode:"))
        self.combo_tnr = QComboBox()
        self.combo_tnr.addItems(["off", "fast", "high-quality"])
        self.combo_tnr.setCurrentIndex(1)  # fast
        self.combo_tnr.currentIndexChanged.connect(self.trigger_restart)
        cam_layout.addWidget(self.combo_tnr)

        # TNR Strength
        cam_layout.addWidget(QLabel("TNR Strength:"))
        tnr_layout = QHBoxLayout()
        self.tnr_str_slider = QSlider(Qt.Horizontal)
        self.tnr_str_slider.setMinimum(0)
        self.tnr_str_slider.setMaximum(10)  # 0.0 to 1.0
        self.tnr_str_slider.setValue(5)
        self.tnr_str_slider.sliderReleased.connect(self.trigger_restart)
        self.lbl_tnr_val = QLabel(str(self.tnr_str_slider.value() / 10.0))
        self.tnr_str_slider.valueChanged.connect(
            lambda v: self.lbl_tnr_val.setText(str(v / 10.0)))
        tnr_layout.addWidget(self.tnr_str_slider)
        tnr_layout.addWidget(self.lbl_tnr_val)
        cam_layout.addLayout(tnr_layout)

        # Edge Enhancement Mode
        cam_layout.addWidget(QLabel("Edge Enhancement Mode:"))
        self.combo_ee = QComboBox()
        self.combo_ee.addItems(["off", "fast", "high-quality"])
        self.combo_ee.setCurrentIndex(1)  # fast
        self.combo_ee.currentIndexChanged.connect(self.trigger_restart)
        cam_layout.addWidget(self.combo_ee)

        # Edge Enhancement Strength
        cam_layout.addWidget(QLabel("Edge Enhancement Strength:"))
        ee_layout = QHBoxLayout()
        self.ee_str_slider = QSlider(Qt.Horizontal)
        self.ee_str_slider.setMinimum(0)
        self.ee_str_slider.setMaximum(10)  # 0.0 to 1.0
        self.ee_str_slider.setValue(5)
        self.ee_str_slider.sliderReleased.connect(self.trigger_restart)
        self.lbl_ee_val = QLabel(str(self.ee_str_slider.value() / 10.0))
        self.ee_str_slider.valueChanged.connect(
            lambda v: self.lbl_ee_val.setText(str(v / 10.0)))
        ee_layout.addWidget(self.ee_str_slider)
        ee_layout.addWidget(self.lbl_ee_val)
        cam_layout.addLayout(ee_layout)

        # Flip Controls
        flip_layout = QHBoxLayout()
        self.chk_h_flip = QCheckBox("Horizontal Flip")
        self.chk_h_flip.stateChanged.connect(self.trigger_restart)
        flip_layout.addWidget(self.chk_h_flip)

        self.chk_v_flip = QCheckBox("Vertical Flip")
        self.chk_v_flip.stateChanged.connect(self.trigger_restart)
        flip_layout.addWidget(self.chk_v_flip)
        cam_layout.addLayout(flip_layout)

        cam_group.setLayout(cam_layout)
        left_panel.addWidget(cam_group)
        left_panel.addStretch()

        # --- CENTER: Video Feed ---
        video_container = QVBoxLayout()
        self.image_label = VideoLabel("Initializing Camera...")
        self.image_label.setFixedSize(DISPLAY_WIDTH, DISPLAY_HEIGHT)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(
            "background-color: #222; color: #EEE; border: 2px solid #555;"
        )
        video_container.addWidget(self.image_label)
        main_row.addLayout(video_container, stretch=3)

        # --- RIGHT: Data & Capture Settings ---
        right_panel = QVBoxLayout()
        right_panel.setSpacing(15)
        main_row.addLayout(right_panel, stretch=1)

        # 2. Data/Format Settings
        data_group = QGroupBox("Data Management")
        data_layout = QVBoxLayout()

        self.lbl_dir = QLabel(f"Save Path:\n{self.save_dir}")
        self.lbl_dir.setWordWrap(True)
        self.lbl_dir.setStyleSheet("font-size: 10px; color: gray;")
        data_layout.addWidget(self.lbl_dir)

        btn_dir = QPushButton("Change Directory")
        btn_dir.clicked.connect(self.select_directory)
        data_layout.addWidget(btn_dir)

        # --- PREFIX INPUT ---
        data_layout.addWidget(QLabel("Filename Prefix (Optional):"))
        self.txt_prefix = QLineEdit()
        self.txt_prefix.setPlaceholderText("e.g. data_ or leave empty")
        self.txt_prefix.textChanged.connect(self.update_filename_counter)
        # Prevent input box from grabbing focus and blocking shortcuts
        self.txt_prefix.returnPressed.connect(self.txt_prefix.clearFocus)
        data_layout.addWidget(self.txt_prefix)
        
        # Helper label
        lbl_hint = QLabel("(Press Enter to set prefix and enable shortcuts)")
        lbl_hint.setStyleSheet(
            "font-size: 10px; color: gray; font-style: italic;")
        data_layout.addWidget(lbl_hint)

        # --- NEW FORMAT SELECTOR ---
        data_layout.addWidget(QLabel("Image Format:"))
        self.combo_format = QComboBox()
        # Added tiff and bmp. Note: png is lossless by default.
        self.combo_format.addItems(["jpg", "png", "tiff", "bmp"])
        self.combo_format.setCurrentText("png")
        self.combo_format.currentTextChanged.connect(
            self.update_filename_counter
        )
        data_layout.addWidget(self.combo_format)

        data_group.setLayout(data_layout)
        right_panel.addWidget(data_group)

        # 3. Capture Controls
        cap_group = QGroupBox("Capture")
        cap_layout = QVBoxLayout()
        self.btn_capture = QPushButton("CAPTURE FRAME")
        self.btn_capture.setMinimumHeight(60)
        self.btn_capture.setStyleSheet(
            "background-color: #2e7d32; color: white; "
            "font-weight: bold; font-size: 14px;"
        )
        self.btn_capture.clicked.connect(self.save_image)
        cap_layout.addWidget(self.btn_capture)

        self.btn_reset_roi = QPushButton("Reset ROI")
        self.btn_reset_roi.clicked.connect(self.reset_roi)
        cap_layout.addWidget(self.btn_reset_roi)

        # --- ROI SIZE SELECTOR ---
        cap_layout.addWidget(QLabel("ROI Size:"))
        self.combo_roi_size = QComboBox()
        self.combo_roi_size.addItems(
            ["Free Select", "224x224", "448x448", "896x896"]
        )
        self.combo_roi_size.currentTextChanged.connect(self.update_roi_size)
        cap_layout.addWidget(self.combo_roi_size)

        self.lbl_counter = QLabel("Next Filename: ...")
        self.lbl_counter.setAlignment(Qt.AlignCenter)
        cap_layout.addWidget(self.lbl_counter)
        cap_group.setLayout(cap_layout)
        right_panel.addWidget(cap_group)

        right_panel.addStretch()

    def update_image(self, cv_img):
        """Update the image label with the new frame."""
        self.current_frame = cv_img
        
        # Resize for display (DISPLAY_WIDTH, DISPLAY_HEIGHT)
        display_frame = cv2.resize(cv_img, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
        
        rgb_img = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_img.shape
        qt_img = QImage(rgb_img.data, w, h, ch * w, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qt_img))

    def trigger_restart(self):
        """Restart the video thread with new settings."""
        val = self.exp_slider.value()
        min_exp = CAM_CONF["exposure_min"]
        max_exp = int(min_exp + (val * CAM_CONF["exposure_multiplier"]))

        gain_val = self.gain_slider.value() / 10.0
        saturation = self.sat_slider.value() / 10.0
        wb_mode = self.combo_wb.currentIndex()
        tnr_mode = self.combo_tnr.currentIndex()
        tnr_strength = self.tnr_str_slider.value() / 10.0
        ee_mode = self.combo_ee.currentIndex()
        ee_strength = self.ee_str_slider.value() / 10.0
        h_flip = self.chk_h_flip.isChecked()
        v_flip = self.chk_v_flip.isChecked()

        self.image_label.setText("Applying Settings...")
        self.thread.update_settings(
            (min_exp, max_exp),
            (gain_val, gain_val),
            self.chk_ae_lock.isChecked(),
            self.chk_awb_lock.isChecked(),
            saturation,
            wb_mode,
            tnr_mode,
            tnr_strength,
            ee_mode,
            ee_strength,
            h_flip,
            v_flip,
        )

    def select_directory(self):
        """Open a dialog to select the save directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Save Directory"
        )
        if directory:
            self.save_dir = directory
            self.lbl_dir.setText(f"Save Path:\n{self.save_dir}")
            self.update_filename_counter()

    def get_next_index(self, directory, prefix, fmt):
        """Helper to find the next available index in a directory."""
        if not os.path.exists(directory):
            return 1
            
        existing_files = os.listdir(directory)
        max_idx = 0

        for f in existing_files:
            if f.endswith(f".{fmt}"):
                name_part = f[: -len(fmt) - 1]  # remove extension and dot

                if prefix:
                    if name_part.startswith(prefix):
                        # Check if the rest is a number
                        suffix = name_part[len(prefix) :]
                        if suffix.isdigit():
                            try:
                                idx = int(suffix)
                                if idx > max_idx:
                                    max_idx = idx
                            except ValueError:
                                pass
                else:
                    # No prefix, check if the whole name is a number
                    if name_part.isdigit():
                        try:
                            idx = int(name_part)
                            if idx > max_idx:
                                max_idx = idx
                        except ValueError:
                            pass
        return max_idx + 1

    def update_filename_counter(self):
        """Recalculate the next index based on SELECTED extensionn & prefix."""
        fmt = self.combo_format.currentText()
        prefix = self.txt_prefix.text().strip()
        idx = self.get_next_index(self.save_dir, prefix, fmt)
        self.capture_count = idx
        self.lbl_counter.setText(
            f"Next: {prefix}{self.capture_count:04d}.{fmt}"
        )

    def reset_roi(self):
        """Reset the ROI selection."""
        self.image_label.clear_roi()
        self.combo_roi_size.setCurrentIndex(0)  # Reset to Free Select

    def update_roi_size(self, text):
        """Update ROI size based on selection."""
        if text == "Free Select":
            return
        try:
            w, h = map(int, text.split("x"))
            self.image_label.set_fixed_roi(w, h)
        except ValueError:
            pass

    def _save_frame_to_path(self, path):
        """Internal method to save the frame to the given path."""
        fmt = self.combo_format.currentText()
        img_to_save = self.current_frame
        
        # --- ROI CROP LOGIC ---
        roi = self.image_label.get_roi()
        if roi:
            x, y, w, h = roi
            # Scale coordinates
            # current_frame is DEFAULT_WIDTH x DEFAULT_HEIGHT (1280x720)
            # display is DISPLAY_WIDTH x DISPLAY_HEIGHT (960x540)
            scale_x = DEFAULT_WIDTH / DISPLAY_WIDTH
            scale_y = DEFAULT_HEIGHT / DISPLAY_HEIGHT

            real_x = int(round(x * scale_x))
            real_y = int(round(y * scale_y))
            real_w = int(round(w * scale_x))
            real_h = int(round(h * scale_y))

            # If a strict ROI size is selected, enforce it exactly (ignoring rounding drift)
            # unless it goes out of bounds.
            current_roi_selection = self.combo_roi_size.currentText()
            if current_roi_selection != "Free Select":
                try:
                    target_w, target_h = map(int, current_roi_selection.split("x"))
                    
                    # Calculate center of the current rounded ROI
                    center_x = real_x + (real_w / 2.0)
                    center_y = real_y + (real_h / 2.0)

                    # Update dimensions
                    real_w = target_w
                    real_h = target_h

                    # Recalculate top-left to keep centered
                    real_x = int(round(center_x - (real_w / 2.0)))
                    real_y = int(round(center_y - (real_h / 2.0)))

                except ValueError:
                    pass

            # Clamp
            real_x = max(0, real_x)
            real_y = max(0, real_y)
            real_w = min(DEFAULT_WIDTH - real_x, real_w)
            real_h = min(DEFAULT_HEIGHT - real_y, real_h)

            if real_w > 0 and real_h > 0:
                img_to_save = img_to_save[
                    real_y : real_y + real_h, real_x : real_x + real_w
                ]

        # --- HIGH QUALITY SAVING LOGIC ---
        params = []
        if fmt == "jpg":
            # Quality 0-100 (Default is 95). We set 100 for AI Data.
            params = [cv2.IMWRITE_JPEG_QUALITY, 100]
        elif fmt == "png":
            # Compression 0-9 (Default is 3). 0 is faster/larger.
            # PNG is lossless, so quality isn't lost, just size.
            params = [cv2.IMWRITE_PNG_COMPRESSION, 3]

        cv2.imwrite(path, img_to_save, params)
        print(f"Saved: {path}")


    def save_image(self):
        """Save the current frame to the selected directory."""
        if self.current_frame is None:
            return

        fmt = self.combo_format.currentText()
        prefix = self.txt_prefix.text().strip()
        idx = self.get_next_index(self.save_dir, prefix, fmt)
        filename = f"{prefix}{idx:04d}.{fmt}"
        path = os.path.join(self.save_dir, filename)

        self._save_frame_to_path(path)
        self.update_filename_counter()
