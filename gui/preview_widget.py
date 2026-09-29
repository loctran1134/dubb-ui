from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QSizePolicy
)
from PyQt6.QtGui import QPainter, QColor, QImage, QPen
from PyQt6.QtCore import Qt, QRectF, QSize, pyqtSignal
import qtawesome as qta
from core.timecode import Timecode
from engine.player import PlaybackController

class VideoCanvas(QWidget):
    """
    OpenCut Video Preview Canvas.
    Renders composited frames centered with precise 1px hairline border.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_frame: QImage = None
        self.aspect_ratio: float = 16.0 / 9.0
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(320, 180)

    def set_frame(self, frame: QImage):
        self.current_frame = frame
        if frame and not frame.isNull() and frame.height() > 0:
            self.aspect_ratio = frame.width() / frame.height()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        # Deep neutral viewport
        painter.fillRect(self.rect(), QColor(9, 9, 11))

        w = self.width()
        h = self.height()
        view_ratio = w / h if h > 0 else 1.0

        padding = 16
        if view_ratio > self.aspect_ratio:
            fit_h = h - padding * 2
            fit_w = fit_h * self.aspect_ratio
        else:
            fit_w = w - padding * 2
            fit_h = fit_w / self.aspect_ratio

        x = (w - fit_w) / 2.0
        y = (h - fit_h) / 2.0
        target_rect = QRectF(x, y, fit_w, fit_h)

        if self.current_frame and not self.current_frame.isNull():
            painter.drawImage(target_rect, self.current_frame)
        else:
            # Blank canvas with subtle placeholder
            painter.fillRect(target_rect, QColor(14, 14, 17))
            painter.setPen(QColor(60, 60, 70))
            painter.drawText(target_rect, Qt.AlignmentFlag.AlignCenter, "OpenCut Preview")

        # Hairline canvas border
        painter.setPen(QPen(QColor(36, 36, 42), 1))
        painter.drawRect(target_rect)
        painter.end()

class PreviewWidget(QWidget):
    """
    OpenCut PreviewPanel matching preview/components/index.tsx & toolbar.tsx:
    - Centered Canvas
    - Bottom PreviewToolbar: Left Timecode, Center Play/Pause button, Right Zoom/Fullscreen.
    """
    def __init__(self, player: PlaybackController, parent=None):
        super().__init__(parent)
        self.player = player
        self.timecode = Timecode(player.timeline.project.fps)

        self.setObjectName("OpenCutPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Viewport Canvas
        self.canvas = VideoCanvas(self)
        layout.addWidget(self.canvas, 1)

        # Bottom PreviewToolbar (OpenCut 3-column layout)
        toolbar = QWidget()
        toolbar.setStyleSheet("background-color: #09090b; border-top: 1px solid #1f1f24; min-height: 40px; max-height: 40px; padding: 0px 14px;")
        t_layout = QHBoxLayout(toolbar)
        t_layout.setContentsMargins(4, 2, 4, 2)

        # Column 1: TimecodeDisplay (Monospace text-[0.8rem])
        self.lbl_timecode = QLabel("00:00:00:00 / 00:00:00:00")
        self.lbl_timecode.setStyleSheet("""
            color: #d4d4d8;
            font-family: "Consolas", "Courier New", monospace;
            font-size: 11px;
            font-weight: 500;
        """)
        t_layout.addWidget(self.lbl_timecode)

        t_layout.addStretch()

        # Column 2: Play/Pause button (OpenCut PlayPauseButton: size icon, no text)
        btn_prev = QPushButton()
        btn_prev.setObjectName("GhostIconButton")
        btn_prev.setIcon(qta.icon("fa5s.step-backward", color="#a1a1aa"))
        btn_prev.setIconSize(QSize(12, 12))
        btn_prev.setToolTip("Previous Frame (Left)")
        btn_prev.clicked.connect(self.player.step_backward)
        t_layout.addWidget(btn_prev)

        self.btn_play = QPushButton()
        self.btn_play.setObjectName("GhostIconButton")
        self.btn_play.setIcon(qta.icon("fa5s.play", color="#ffffff"))
        self.btn_play.setIconSize(QSize(14, 14))
        self.btn_play.setToolTip("Play / Pause (Space)")
        self.btn_play.clicked.connect(self.player.toggle_play)
        t_layout.addWidget(self.btn_play)

        btn_next = QPushButton()
        btn_next.setObjectName("GhostIconButton")
        btn_next.setIcon(qta.icon("fa5s.step-forward", color="#a1a1aa"))
        btn_next.setIconSize(QSize(12, 12))
        btn_next.setToolTip("Next Frame (Right)")
        btn_next.clicked.connect(self.player.step_forward)
        t_layout.addWidget(btn_next)

        t_layout.addStretch()

        # Column 3: Canvas resolution & Fullscreen
        proj = self.player.timeline.project
        self.lbl_res = QLabel(f"{proj.width}x{proj.height}")
        self.lbl_res.setStyleSheet("color: #71717a; font-size: 11px;")
        t_layout.addWidget(self.lbl_res)

        btn_fs = QPushButton()
        btn_fs.setObjectName("GhostIconButton")
        btn_fs.setIcon(qta.icon("fa5s.expand", color="#a1a1aa"))
        btn_fs.setIconSize(QSize(12, 12))
        btn_fs.setToolTip("Toggle Fullscreen")
        t_layout.addWidget(btn_fs)

        layout.addWidget(toolbar)

        self.player.playback_state_changed.connect(self._on_playback_state)
        self.player.time_changed.connect(self._on_time_changed)

    def update_frame(self, frame: QImage):
        self.canvas.set_frame(frame)

    def _on_playback_state(self, is_playing: bool):
        icon_name = "fa5s.pause" if is_playing else "fa5s.play"
        self.btn_play.setIcon(qta.icon(icon_name, color="#ffffff"))

    def _on_time_changed(self, current_time: float):
        total_time = self.player.timeline.duration
        cur_str = self.timecode.format_time(current_time)
        tot_str = self.timecode.format_time(total_time)
        self.lbl_timecode.setText(f"{cur_str} / {tot_str}")
