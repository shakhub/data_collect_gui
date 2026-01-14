from PyQt5.QtCore import QPoint, QRect, Qt
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtWidgets import QLabel

from src.config import (
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
)


class VideoLabel(QLabel):
    """Custom QLabel to handle ROI selection."""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.roi_start = QPoint(0, 0)
        self.roi_end = QPoint(0, 0)
        self.is_selecting = False
        self.has_roi = False
        # Enable mouse tracking if needed, though press/drag works without it
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        if self.has_roi:
            return
        if event.button() == Qt.LeftButton:
            self.roi_start = event.pos()
            self.roi_end = event.pos()
            self.is_selecting = True
            self.has_roi = False
            self.fixed_roi_text = None
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            # Enforce square aspect ratio
            curr_pos = event.pos()
            dx = curr_pos.x() - self.roi_start.x()
            dy = curr_pos.y() - self.roi_start.y()

            # Use the larger dimension to determine square size
            side = max(abs(dx), abs(dy))

            # Determine direction
            sign_x = 1 if dx >= 0 else -1
            sign_y = 1 if dy >= 0 else -1

            new_x = self.roi_start.x() + (side * sign_x)
            new_y = self.roi_start.y() + (side * sign_y)

            # Clamp to window boundaries
            new_x = max(0, min(new_x, self.width()))
            new_y = max(0, min(new_y, self.height()))

            self.roi_end = QPoint(new_x, new_y)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_selecting = False
            # Finalize square
            rect = QRect(self.roi_start, self.roi_end).normalized()
            side = max(rect.width(), rect.height())
            # Center the square on the dragged area or just force it?
            # Let's force the square based on start point and direction
            dx = self.roi_end.x() - self.roi_start.x()
            dy = self.roi_end.y() - self.roi_start.y()
            sign_x = 1 if dx >= 0 else -1
            sign_y = 1 if dy >= 0 else -1

            self.roi_end = QPoint(
                self.roi_start.x() + (side - 1) * sign_x,
                self.roi_start.y() + (side - 1) * sign_y,
            )

            rect = QRect(self.roi_start, self.roi_end).normalized()
            if rect.width() > 10:
                self.has_roi = True
            else:
                self.has_roi = False
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.is_selecting or self.has_roi:
            painter = QPainter(self)
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            rect = QRect(self.roi_start, self.roi_end).normalized()

            painter.drawRect(rect)

            # Draw dimensions
            if hasattr(self, 'fixed_roi_text') and self.fixed_roi_text:
                text = self.fixed_roi_text
            else:
                scale_x = DEFAULT_WIDTH / DISPLAY_WIDTH
                scale_y = DEFAULT_HEIGHT / DISPLAY_HEIGHT
                
                real_w = int(round(rect.width() * scale_x))
                real_h = int(round(rect.height() * scale_y))

                text = f"{real_w}x{real_h} px"
            
            painter.setPen(QPen(Qt.yellow, 1, Qt.SolidLine))
            painter.drawText(rect.topLeft() + QPoint(5, -5), text)

    def set_fixed_roi(self, w, h):
        """Set a fixed ROI centered in the view."""
        scale_x = DISPLAY_WIDTH / DEFAULT_WIDTH
        scale_y = DISPLAY_HEIGHT / DEFAULT_HEIGHT
        
        disp_w = int(round(w * scale_x))
        disp_h = int(round(h * scale_y))

        center_x = self.width() // 2
        center_y = self.height() // 2

        self.roi_start = QPoint(center_x - disp_w // 2, center_y - disp_h // 2)
        # Subtract 1 to ensure QRect(start, end).width() == disp_w
        self.roi_end = QPoint(
            self.roi_start.x() + disp_w - 1, self.roi_start.y() + disp_h - 1
        )
        self.has_roi = True
        self.fixed_roi_text = f"{w}x{h} px"
        self.update()

    def get_roi(self):
        if self.has_roi:
            rect = QRect(self.roi_start, self.roi_end).normalized()
            return (rect.x(), rect.y(), rect.width(), rect.height())
        return None

    def clear_roi(self):
        self.has_roi = False
        self.fixed_roi_text = None
        self.update()
