import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QSplitter, QDialog
)
from PyQt6.QtGui import QKeySequence, QShortcut, QIcon
from PyQt6.QtCore import Qt, QSize
import qtawesome as qta

from core.models import Timeline, Project, Clip
from engine.player import PlaybackController
from engine.compositor import Compositor
from engine.media_reader import MediaReader
from gui.preview_widget import PreviewWidget
from gui.inspector_widget import InspectorWidget
from gui.media_library_widget import MediaLibraryWidget
from gui.timeline.timeline_view import TimelineView
from gui.export_dialog import ExportDialog
from gui.styles import OPENCUT_THEME_QSS

class ShortcutsDialog(QDialog):
    """
    OpenCut Keyboard Shortcuts modal dialog.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Shortcuts")
        self.setFixedSize(360, 290)
        self.setStyleSheet("background-color: #09090b; border: 1px solid #1f1f24; color: #f4f4f5;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl_title = QLabel("Keyboard Shortcuts")
        lbl_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #ffffff;")
        layout.addWidget(lbl_title)

        shortcuts = [
            ("Play / Pause", "Space"),
            ("Split Element", "S / Ctrl+B"),
            ("Delete Element", "Delete / Backspace"),
            ("Step 1 Frame Back", "Left Arrow (←)"),
            ("Step 1 Frame Forward", "Right Arrow (→)"),
            ("Zoom In", "Ctrl + '+'"),
            ("Zoom Out", "Ctrl + '-'"),
        ]

        for action, key in shortcuts:
            row = QHBoxLayout()
            lbl_act = QLabel(action)
            lbl_act.setStyleSheet("color: #a1a1aa; font-size: 11px;")
            row.addWidget(lbl_act)

            lbl_key = QLabel(key)
            lbl_key.setStyleSheet("""
                background-color: #18181b;
                color: #e4e4e7;
                font-family: monospace;
                font-size: 11px;
                padding: 2px 7px;
                border-radius: 4px;
                border: 1px solid #27272a;
            """)
            row.addWidget(lbl_key)
            layout.addLayout(row)

        layout.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

class MainWindow(QMainWindow):
    """
    OpenCut Main Window.
    Clones the exact EditorHeader, ResizablePanelGroup layout, styling, and interactions of OpenCut.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenCut")
        self.resize(1400, 880)
        self.setMinimumSize(1024, 650)
        self.setStyleSheet(OPENCUT_THEME_QSS)

        # Core Engine
        self.project = Project(name="Untitled project", width=1920, height=1080, fps=30.0)
        self.timeline = Timeline(self.project)
        self.player = PlaybackController(self.timeline, self)
        self.compositor = Compositor(self.timeline)

        self._setup_ui()
        self._setup_shortcuts()
        self._connect_signals()

        self._refresh_preview()

    def _setup_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(6)

        # 1. OpenCut EditorHeader (h-[3.4rem])
        header = QWidget()
        header.setObjectName("EditorHeader")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 0, 12, 0)
        h_layout.setSpacing(10)

        # Left: OpenCut Logo Icon + Name
        logo_container = QWidget()
        l_layout = QHBoxLayout(logo_container)
        l_layout.setContentsMargins(0, 0, 0, 0)
        l_layout.setSpacing(6)

        lbl_logo_icon = QLabel()
        lbl_logo_icon.setPixmap(qta.icon("fa5s.cut", color="#009dff").pixmap(16, 16))
        l_layout.addWidget(lbl_logo_icon)

        lbl_logo = QLabel("OpenCut")
        lbl_logo.setObjectName("LogoText")
        l_layout.addWidget(lbl_logo)
        h_layout.addWidget(logo_container)

        # Editable Project Name (OpenCut EditableProjectName)
        self.txt_project_name = QLineEdit(self.project.name)
        self.txt_project_name.setObjectName("EditableProjectName")
        self.txt_project_name.setFixedWidth(190)
        self.txt_project_name.setCursorPosition(0)
        self.txt_project_name.editingFinished.connect(self._on_project_renamed)
        h_layout.addWidget(self.txt_project_name)

        h_layout.addStretch()

        # Canvas Aspect Ratio Selector
        self.cb_aspect = QComboBox()
        self.cb_aspect.addItems(["16:9 Landscape (1920x1080)", "9:16 TikTok (1080x1920)", "1:1 Square (1080x1080)"])
        self.cb_aspect.currentIndexChanged.connect(self._on_aspect_ratio_changed)
        h_layout.addWidget(self.cb_aspect)

        # Shortcuts Icon Button
        self.btn_shortcuts = QPushButton()
        self.btn_shortcuts.setObjectName("GhostIconButton")
        self.btn_shortcuts.setIcon(qta.icon("fa5s.keyboard", color="#a1a1aa"))
        self.btn_shortcuts.setIconSize(QSize(13, 13))
        self.btn_shortcuts.setToolTip("Shortcuts")
        self.btn_shortcuts.clicked.connect(self._open_shortcuts_dialog)
        h_layout.addWidget(self.btn_shortcuts)

        # Signature OpenCut Export Button (#009dff)
        self.btn_export = QPushButton("Export")
        self.btn_export.setObjectName("ExportButton")
        self.btn_export.setIcon(qta.icon("fa5s.arrow-circle-up", color="#ffffff"))
        self.btn_export.setIconSize(QSize(12, 12))
        self.btn_export.clicked.connect(self._open_export_dialog)
        h_layout.addWidget(self.btn_export)

        root_layout.addWidget(header)

        # 2. Resizable Panels Body (Monolithic seamless pro layout)
        body_container = QWidget()
        b_layout = QVBoxLayout(body_container)
        b_layout.setContentsMargins(0, 0, 0, 0)
        b_layout.setSpacing(0)

        # Vertical Splitter (Upper Panels vs Lower Timeline)
        self.v_splitter = QSplitter(Qt.Orientation.Vertical)
        self.v_splitter.setHandleWidth(1)

        # Upper Horizontal Splitter (Assets | Preview | Properties)
        self.h_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.h_splitter.setHandleWidth(1)

        self.media_panel = MediaLibraryWidget(self)
        self.preview_panel = PreviewWidget(self.player, self)
        self.inspector_panel = InspectorWidget(self)

        self.h_splitter.addWidget(self.media_panel)
        self.h_splitter.addWidget(self.preview_panel)
        self.h_splitter.addWidget(self.inspector_panel)
        self.h_splitter.setSizes([310, 730, 360])

        self.v_splitter.addWidget(self.h_splitter)

        # Lower Timeline Panel
        self.timeline_panel = TimelineView(self.timeline, self)
        self.v_splitter.addWidget(self.timeline_panel)
        self.v_splitter.setSizes([520, 300])

        b_layout.addWidget(self.v_splitter, 1)
        root_layout.addWidget(body_container, 1)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self.player.toggle_play)
        QShortcut(QKeySequence(Qt.Key.Key_S), self, self.timeline_panel.split_active_clip)
        QShortcut(QKeySequence("Ctrl+B"), self, self.timeline_panel.split_active_clip)
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self, self.timeline_panel.delete_selected_clip)
        QShortcut(QKeySequence(Qt.Key.Key_Backspace), self, self.timeline_panel.delete_selected_clip)
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, self.player.step_backward)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, self.player.step_forward)

    def _connect_signals(self):
        self.media_panel.media_add_requested.connect(self._add_media_to_timeline)
        self.media_panel.clip_add_requested.connect(self._add_clip_to_timeline)
        self.media_panel.filter_apply_requested.connect(self._apply_filter_to_selected_clip)
        self.media_panel.settings_changed.connect(self._on_project_settings_changed)
        self.player.time_changed.connect(self._on_time_changed)
        self.timeline_panel.time_scrubbed.connect(self.player.seek)
        self.timeline_panel.clip_selected.connect(self._on_clip_selected)
        self.timeline_panel.timeline_changed.connect(self._refresh_preview)
        self.inspector_panel.property_changed.connect(self._refresh_preview)
        self.inspector_panel.geometry_changed.connect(self._on_clip_geometry_changed)

    def _on_project_renamed(self):
        new_name = self.txt_project_name.text().strip()
        if new_name:
            self.project.name = new_name
            self.setWindowTitle(f"{new_name} - OpenCut")

    def _on_clip_selected(self, clip):
        self.inspector_panel.inspect_clip(clip)
        if clip is not None:
            # If playhead is outside the clip, seek to start_time so preview updates immediately
            if not clip.contains_time(self.timeline.playhead_time):
                self.player.seek(clip.start_time)
            else:
                self._refresh_preview()

    def _on_clip_geometry_changed(self):
        self.timeline_panel.rebuild_timeline()
        self._refresh_preview()

    def _add_media_to_timeline(self, media_path: str):
        reader = MediaReader(media_path)
        info = reader.info
        duration = max(1.0, info.duration if info.duration > 0 else 5.0)

        media_type = "video" if info.has_video else "audio"
        target_track = self.timeline.get_default_track(media_type)

        start_time = self.timeline.playhead_time
        new_clip = Clip(
            media_path=media_path,
            media_type=media_type,
            start_time=start_time,
            duration=duration,
            source_in=0.0,
            source_out=duration
        )
        target_track.add_clip(new_clip)

        self.timeline_panel.rebuild_timeline()
        self.timeline_panel.select_clip(new_clip.clip_id)
        self.player.seek(start_time)
        self._refresh_preview()

    def _add_clip_to_timeline(self, clip: Clip):
        clip.start_time = self.timeline.playhead_time
        target_track = self.timeline.get_default_track(clip.media_type)
        target_track.add_clip(clip)

        self.timeline_panel.rebuild_timeline()
        self.timeline_panel.select_clip(clip.clip_id)
        self.player.seek(clip.start_time)
        self._refresh_preview()

    def _apply_filter_to_selected_clip(self, filter_id: str):
        target_clip = None
        if self.timeline.selected_clip_id:
            found = self.timeline.find_clip_by_id(self.timeline.selected_clip_id)
            if found:
                target_clip = found[1]

        if not target_clip:
            for track in self.timeline.tracks:
                if track.track_type == "video":
                    c = track.get_clip_at(self.timeline.playhead_time)
                    if c:
                        target_clip = c
                        break

        if target_clip:
            target_clip.properties.filter_type = filter_id
            self.inspector_panel.inspect_clip(target_clip)
            self._refresh_preview()

    def _on_project_settings_changed(self, cfg: dict):
        if "width" in cfg and "height" in cfg:
            self.project.width = cfg["width"]
            self.project.height = cfg["height"]
            self.preview_panel.lbl_res.setText(f"{self.project.width}x{self.project.height}")
        if "fps" in cfg:
            self.project.fps = cfg["fps"]
        self._refresh_preview()

    def _on_time_changed(self, time_sec: float):
        self.timeline_panel.update_playhead(time_sec)
        self._refresh_preview()

    def _refresh_preview(self):
        current_time = self.timeline.playhead_time
        frame = self.compositor.render_frame(current_time)
        self.preview_panel.update_frame(frame)

    def _on_aspect_ratio_changed(self, index: int):
        if index == 0:
            self.project.width = 1920
            self.project.height = 1080
        elif index == 1:
            self.project.width = 1080
            self.project.height = 1920
        elif index == 2:
            self.project.width = 1080
            self.project.height = 1080

        self.preview_panel.lbl_res.setText(f"{self.project.width}x{self.project.height}")
        self._refresh_preview()

    def _open_export_dialog(self):
        dlg = ExportDialog(self.timeline, self)
        dlg.exec()

    def _open_shortcuts_dialog(self):
        dlg = ShortcutsDialog(self)
        dlg.exec()

    def closeEvent(self, event):
        self.player.pause()
        self.compositor.cleanup()
        super().closeEvent(event)
