from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider,
    QGraphicsView, QGraphicsScene, QGraphicsLineItem, QFrame, QSizePolicy
)
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
import qtawesome as qta

from core.models import Timeline, Clip, Track
from core.timecode import Timecode
from gui.timeline.ruler import TimeRuler
from gui.timeline.clip_item import ClipItem

class TrackHeadersWidget(QWidget):
    """
    OpenCut track header panel on the left side of the timeline.
    Shows track name badges, mute, lock, and visibility indicators.
    """
    def __init__(self, timeline: Timeline, track_height: float = 48.0, parent=None):
        super().__init__(parent)
        self.timeline = timeline
        self.track_height = track_height
        self.setFixedWidth(145)
        self.setStyleSheet("background-color: #09090b; border-right: 1px solid #1f1f24;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        for i, track in enumerate(self.timeline.tracks):
            y = int(i * self.track_height)
            h = int(self.track_height)

            # Lane border
            painter.setPen(QColor(27, 27, 34))
            painter.drawLine(0, y + h - 1, self.width(), y + h - 1)

            # Track type badge & indicator
            is_video = track.track_type == "video"
            badge_color = QColor(59, 130, 246) if is_video else QColor(143, 93, 186)

            # Color pill indicator
            painter.setBrush(QBrush(badge_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(8, y + 14, 3, h - 28), 1.5, 1.5)

            # Track label
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
            painter.setPen(QColor(228, 228, 231))
            painter.drawText(18, y + 23, track.name)

            # Category sub-label
            painter.setFont(QFont("Segoe UI", 7))
            painter.setPen(QColor(113, 113, 122))
            painter.drawText(18, y + 36, "VIDEO" if is_video else "AUDIO")

        painter.end()

class TimelineView(QWidget):
    """
    OpenCut Timeline Panel.
    Integrates the signature toolbar (Split, Delete, Snap, Zoom), time ruler, track headers, and clip lanes.
    """
    clip_selected = pyqtSignal(object)
    time_scrubbed = pyqtSignal(float)
    timeline_changed = pyqtSignal()

    def __init__(self, timeline: Timeline, parent=None):
        super().__init__(parent)
        self.timeline = timeline
        self.timecode = Timecode(timeline.project.fps)
        self.px_per_sec = 60.0
        self.track_height = 48.0

        self.clip_items: list[ClipItem] = []
        self.playhead_line: QGraphicsLineItem = None

        self.setObjectName("OpenCutPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Timeline Toolbar (Matching OpenCut timeline-toolbar.tsx)
        toolbar = QWidget()
        toolbar.setStyleSheet("background-color: #0d0d0f; border-bottom: 1px solid #1f1f24; min-height: 36px; max-height: 36px;")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(8, 2, 8, 2)
        tb_layout.setSpacing(4)

        # Split Tool (✂️)
        self.btn_split = QPushButton()
        self.btn_split.setObjectName("GhostIconButton")
        self.btn_split.setIcon(qta.icon("fa5s.cut", color="#a1a1aa"))
        self.btn_split.setToolTip("Split Element at Playhead (S)")
        self.btn_split.clicked.connect(self.split_active_clip)
        tb_layout.addWidget(self.btn_split)

        # Delete Tool (🗑️)
        self.btn_delete = QPushButton()
        self.btn_delete.setObjectName("GhostIconButton")
        self.btn_delete.setIcon(qta.icon("fa5s.trash-alt", color="#a1a1aa"))
        self.btn_delete.setToolTip("Delete Element (Delete)")
        self.btn_delete.clicked.connect(self.delete_selected_clip)
        tb_layout.addWidget(self.btn_delete)

        # Snap Toggle Tool (🧲)
        self.btn_snap = QPushButton()
        self.btn_snap.setObjectName("GhostIconButton")
        self.btn_snap.setCheckable(True)
        self.btn_snap.setChecked(True)
        self.btn_snap.setIcon(qta.icon("fa5s.magnet", color="#009dff"))
        self.btn_snap.setToolTip("Toggle Snapping")
        tb_layout.addWidget(self.btn_snap)

        tb_layout.addStretch()

        # Zoom Controls
        self.btn_zoom_out = QPushButton()
        self.btn_zoom_out.setObjectName("GhostIconButton")
        self.btn_zoom_out.setIcon(qta.icon("fa5s.search-minus", color="#a1a1aa"))
        self.btn_zoom_out.clicked.connect(lambda: self.slider_zoom.setValue(self.slider_zoom.value() - 15))
        tb_layout.addWidget(self.btn_zoom_out)

        self.slider_zoom = QSlider(Qt.Orientation.Horizontal)
        self.slider_zoom.setRange(20, 250)
        self.slider_zoom.setValue(int(self.px_per_sec))
        self.slider_zoom.setFixedWidth(90)
        self.slider_zoom.valueChanged.connect(self._on_zoom_changed)
        tb_layout.addWidget(self.slider_zoom)

        self.btn_zoom_in = QPushButton()
        self.btn_zoom_in.setObjectName("GhostIconButton")
        self.btn_zoom_in.setIcon(qta.icon("fa5s.search-plus", color="#a1a1aa"))
        self.btn_zoom_in.clicked.connect(lambda: self.slider_zoom.setValue(self.slider_zoom.value() + 15))
        tb_layout.addWidget(self.btn_zoom_in)

        layout.addWidget(toolbar)

        # 2. Timeline Body (Track Headers on Left + Ruler and Graphic Lanes on Right)
        timeline_body = QWidget()
        body_layout = QHBoxLayout(timeline_body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Left Column: Corner spacer + Track Headers
        left_col = QWidget()
        left_layout = QVBoxLayout(left_col)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        corner_spacer = QWidget()
        corner_spacer.setFixedHeight(26)
        corner_spacer.setStyleSheet("background-color: #09090b; border-bottom: 1px solid #1f1f24;")
        left_layout.addWidget(corner_spacer)

        self.track_headers = TrackHeadersWidget(self.timeline, self.track_height, self)
        left_layout.addWidget(self.track_headers, 1)
        body_layout.addWidget(left_col)

        # Right Column: Time Ruler + Graphics View
        right_col = QWidget()
        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.ruler = TimeRuler(self.timecode, self.px_per_sec, self)
        self.ruler.time_scrubbed.connect(self._on_ruler_scrubbed)
        right_layout.addWidget(self.ruler)

        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QBrush(QColor(9, 9, 11)))
        self.view = QGraphicsView(self.scene)
        self.view.setFrameShape(QFrame.Shape.NoFrame)
        self.view.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Synchronize ruler scroll offset with view scrollbar!
        self.view.horizontalScrollBar().valueChanged.connect(self.ruler.set_scroll_offset)

        self.scene.selectionChanged.connect(self._on_selection_changed)

        right_layout.addWidget(self.view, 1)
        body_layout.addWidget(right_col, 1)

        layout.addWidget(timeline_body, 1)

        self.rebuild_timeline()

    def rebuild_timeline(self):
        prev_selected_id = self.timeline.selected_clip_id

        # Block signals on scene to avoid spurious deselection during clear
        self.scene.blockSignals(True)
        self.scene.clear()
        self.clip_items.clear()

        total_tracks = len(self.timeline.tracks)
        scene_height = total_tracks * self.track_height
        scene_width = max(2000.0, self.timeline.duration * self.px_per_sec + 500)
        self.scene.setSceneRect(0, 0, scene_width, scene_height)

        # Draw subtle track lanes
        for i in range(total_tracks + 1):
            y = i * self.track_height
            self.scene.addLine(0, y, scene_width, y, QPen(QColor(27, 27, 34), 1))

        # Add clips and restore selection
        selected_item = None
        for track_idx, track in enumerate(self.timeline.tracks):
            for clip in track.clips:
                item = ClipItem(clip, track, track_idx, self.px_per_sec, self.track_height)
                item.on_clip_clicked = self._on_clip_item_clicked
                item.on_clip_modified = self._on_clip_item_modified
                self.scene.addItem(item)
                self.clip_items.append(item)
                if clip.clip_id == prev_selected_id:
                    selected_item = item

        # OpenCut Blue Playhead Line (#009dff)
        self.playhead_line = self.scene.addLine(
            0, 0, 0, scene_height,
            QPen(QColor(0, 157, 255), 1.5)
        )
        self.playhead_line.setZValue(100)

        self.scene.blockSignals(False)

        if selected_item:
            selected_item.setSelected(True)
            self.timeline.selected_clip_id = prev_selected_id
            self.clip_selected.emit(selected_item.clip)
        elif prev_selected_id:
            # Clip might have been deleted
            found = self.timeline.find_clip_by_id(prev_selected_id)
            if not found:
                self.timeline.selected_clip_id = None
                self.clip_selected.emit(None)

        self.update_playhead(self.timeline.playhead_time)
        self.ruler.set_duration(self.timeline.duration)

    def select_clip(self, clip_id: str):
        self.timeline.selected_clip_id = clip_id
        selected_clip = None
        for item in self.clip_items:
            if item.clip.clip_id == clip_id:
                item.setSelected(True)
                selected_clip = item.clip
            else:
                item.setSelected(False)
        self.clip_selected.emit(selected_clip)

    def _on_clip_item_clicked(self, clip: Clip, click_time: float):
        self.timeline.selected_clip_id = clip.clip_id
        self.clip_selected.emit(clip)
        self.update_playhead(click_time)
        self.time_scrubbed.emit(click_time)

    def _on_clip_item_modified(self, clip: Clip):
        self.ruler.set_duration(self.timeline.duration)
        scene_width = max(2000.0, self.timeline.duration * self.px_per_sec + 500)
        self.scene.setSceneRect(0, 0, scene_width, self.scene.height())
        self.timeline_changed.emit()

    def update_playhead(self, time_sec: float):
        x = time_sec * self.px_per_sec
        if self.playhead_line:
            self.playhead_line.setLine(x, 0, x, self.scene.height())
        self.ruler.set_time(time_sec)

    def _on_ruler_scrubbed(self, time_sec: float):
        self.update_playhead(time_sec)
        self.time_scrubbed.emit(time_sec)

    def _on_zoom_changed(self, val: int):
        self.px_per_sec = float(val)
        self.ruler.set_zoom(self.px_per_sec)
        self.rebuild_timeline()

    def _on_selection_changed(self):
        selected = self.scene.selectedItems()
        if selected and isinstance(selected[0], ClipItem):
            clip = selected[0].clip
            self.timeline.selected_clip_id = clip.clip_id
            self.clip_selected.emit(clip)
        else:
            self.timeline.selected_clip_id = None
            self.clip_selected.emit(None)

    def split_active_clip(self):
        if not self.timeline.selected_clip_id:
            return
        split_time = self.timeline.playhead_time
        new_clip = self.timeline.split_clip_at(self.timeline.selected_clip_id, split_time)
        if new_clip:
            self.rebuild_timeline()
            self.select_clip(new_clip.clip_id)
            self.timeline_changed.emit()

    def delete_selected_clip(self):
        if not self.timeline.selected_clip_id:
            return
        found = self.timeline.find_clip_by_id(self.timeline.selected_clip_id)
        if found:
            track, clip = found
            track.remove_clip(clip.clip_id)
            self.timeline.selected_clip_id = None
            self.clip_selected.emit(None)
            self.rebuild_timeline()
            self.timeline_changed.emit()
