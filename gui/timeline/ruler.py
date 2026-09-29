from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF
from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from core.timecode import Timecode

class TimeRuler(QWidget):
    """
    OpenCut Timeline Ruler.
    Features subtle dark tick marks and signature #009dff blue playhead indicator.
    Synchronized with the timeline graphics view scroll offset.
    """
    time_scrubbed = pyqtSignal(float)

    def __init__(self, timecode: Timecode, pixels_per_second: float = 60.0, parent=None):
        super().__init__(parent)
        self.timecode = timecode
        self.px_per_sec = pixels_per_second
        self.current_time = 0.0
        self.total_duration = 60.0
        self.scroll_offset = 0.0
        self.is_scrubbing = False

        self.setFixedHeight(26)
        self.setStyleSheet("background-color: #0d0d0f;")

    def set_zoom(self, px_per_sec: float):
        self.px_per_sec = max(10.0, min(500.0, px_per_sec))
        self.update_geometry()
        self.update()

    def set_time(self, time_sec: float):
        self.current_time = max(0.0, time_sec)
        self.update()

    def set_duration(self, duration: float):
        self.total_duration = max(10.0, duration)
        self.update_geometry()
        self.update()

    def set_scroll_offset(self, offset: float):
        if self.scroll_offset != offset:
            self.scroll_offset = float(offset)
            self.update()

    def update_geometry(self):
        req_width = int(self.total_duration * self.px_per_sec) + 300
        self.setMinimumWidth(req_width)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_scrubbing = True
            self._scrub(event.position().x())

    def mouseMoveEvent(self, event):
        if self.is_scrubbing:
            self._scrub(event.position().x())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_scrubbing = False

    def _scrub(self, x: float):
        target_time = max(0.0, (x + self.scroll_offset) / self.px_per_sec)
        self.current_time = target_time
        self.time_scrubbed.emit(target_time)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Background & separator
        painter.fillRect(self.rect(), QColor(13, 13, 15))
        painter.setPen(QColor(31, 31, 36))
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)

        # Translate painter by scroll offset so ticks align with the timeline view
        painter.save()
        painter.translate(-self.scroll_offset, 0)

        # Step calculation based on zoom
        if self.px_per_sec >= 120:
            major_step = 1.0
            minor_step = 0.2
        elif self.px_per_sec >= 50:
            major_step = 2.0
            minor_step = 0.5
        else:
            major_step = 5.0
            minor_step = 1.0

        view_max_x = self.scroll_offset + self.width() + 100
        view_min_x = max(0.0, self.scroll_offset - 100)

        # Draw minor ticks
        painter.setPen(QPen(QColor(45, 45, 55), 1))
        t = (int(view_min_x / (minor_step * self.px_per_sec))) * minor_step
        while t * self.px_per_sec <= view_max_x:
            x = t * self.px_per_sec
            painter.drawLine(int(x), self.height() - 5, int(x), self.height() - 1)
            t += minor_step

        # Draw major ticks & clean typography timecode
        font = QFont("Segoe UI", 8)
        painter.setFont(font)

        start_major = int(view_min_x / (major_step * self.px_per_sec))
        num_majors = int((view_max_x - view_min_x) / (major_step * self.px_per_sec)) + 3

        for i in range(start_major, start_major + num_majors):
            t_sec = i * major_step
            if t_sec < 0:
                continue
            x = t_sec * self.px_per_sec
            painter.setPen(QPen(QColor(90, 90, 105), 1))
            painter.drawLine(int(x), self.height() - 10, int(x), self.height() - 1)

            time_str = self.timecode.format_short_time(t_sec)
            painter.setPen(QColor(140, 140, 155))
            painter.drawText(int(x) + 4, 14, time_str)

        # Playhead Head in signature OpenCut Blue (#009dff)
        ph_x = self.current_time * self.px_per_sec
        painter.setBrush(QColor(0, 157, 255))
        painter.setPen(Qt.PenStyle.NoPen)

        # Sleek needle bookmark shape
        polygon = QPolygonF([
            QPointF(ph_x - 5, 0),
            QPointF(ph_x + 5, 0),
            QPointF(ph_x + 5, 12),
            QPointF(ph_x, 22),
            QPointF(ph_x - 5, 12),
        ])
        painter.drawPolygon(polygon)

        painter.restore()
        painter.end()
