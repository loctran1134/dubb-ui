import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QFileDialog, QButtonGroup, QFrame, QStackedWidget,
    QScrollArea, QGridLayout, QComboBox, QLineEdit
)
from PyQt6.QtGui import QPixmap, QFont, QColor
from PyQt6.QtCore import Qt, QSize, pyqtSignal
import qtawesome as qta
from engine.media_reader import MediaReader, MediaInfo
from core.models import Clip, ClipProperties

class MediaCardWidget(QWidget):
    """
    OpenCut DraggableItem card representation with 16:9 thumbnail,
    duration badge, filename, and '+' add button.
    Clean borderless layout with subtle hover highlight.
    """
    add_clicked = pyqtSignal(str)

    def __init__(self, media_path: str, thumbnail: QPixmap, info: MediaInfo, parent=None):
        super().__init__(parent)
        self.media_path = media_path
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
                border-radius: 6px;
            }
            QWidget:hover {
                background-color: #16161a;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(10)

        # 16:9 Thumbnail container
        thumb_container = QWidget()
        thumb_container.setFixedSize(68, 38)
        t_layout = QVBoxLayout(thumb_container)
        t_layout.setContentsMargins(0, 0, 0, 0)

        lbl_thumb = QLabel()
        lbl_thumb.setFixedSize(68, 38)
        lbl_thumb.setScaledContents(True)
        lbl_thumb.setPixmap(thumbnail)
        lbl_thumb.setStyleSheet("border-radius: 3px; background-color: #000000;")
        t_layout.addWidget(lbl_thumb)
        layout.addWidget(thumb_container)

        # Details
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        lbl_name = QLabel(info.filename)
        lbl_name.setStyleSheet("font-weight: 500; color: #f4f4f5; font-size: 11px;")
        info_layout.addWidget(lbl_name)

        desc = f"{info.duration:.1f}s"
        if info.has_video:
            desc += f" • {info.width}x{info.height}"
        else:
            desc += " • Audio"
        lbl_sub = QLabel(desc)
        lbl_sub.setStyleSheet("color: #71717a; font-size: 10px;")
        info_layout.addWidget(lbl_sub)
        layout.addLayout(info_layout, 1)

        # Plus button
        btn_add = QPushButton()
        btn_add.setFixedSize(24, 24)
        btn_add.setIcon(qta.icon("fa5s.plus", color="#a1a1aa"))
        btn_add.setIconSize(QSize(10, 10))
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #1f1f24;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #009dff;
                color: #ffffff;
            }
        """)
        btn_add.setToolTip("Add to timeline")
        btn_add.clicked.connect(lambda: self.add_clicked.emit(self.media_path))
        layout.addWidget(btn_add)

class MediaLibraryWidget(QWidget):
    """
    OpenCut Left Assets & Tool Panel.
    Clones OpenCut's exact panel structure (apps/web/src/components/editor/panels/assets):
    - Media (File manager + Dropzone)
    - Sounds (Audio files)
    - Text (OpenCut Default Text element)
    - Stickers (Shapes & Graphics)
    - Effects (OpenCut EffectsRegistry)
    - Transitions (Transitions view)
    - Settings (Project Canvas Settings)
    """
    media_add_requested = pyqtSignal(str)
    clip_add_requested = pyqtSignal(object)
    filter_apply_requested = pyqtSignal(str)
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("OpenCutPanel")
        self.imported_readers: dict[str, MediaReader] = {}

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Vertical Icon TabBar (44px)
        self.tab_bar = QWidget()
        self.tab_bar.setObjectName("AssetsTabBar")
        tb_layout = QVBoxLayout(self.tab_bar)
        tb_layout.setContentsMargins(0, 6, 0, 6)
        tb_layout.setSpacing(3)

        self.tab_group = QButtonGroup(self)
        self.tab_group.setExclusive(True)

        tabs_data = [
            (0, "Media", "fa5s.folder"),
            (1, "Sounds", "fa5s.music"),
            (2, "Text", "fa5s.font"),
            (3, "Stickers", "fa5s.smile"),
            (4, "Effects", "fa5s.magic"),
            (5, "Transitions", "fa5s.exchange-alt"),
            (6, "Settings", "fa5s.cog"),
        ]

        self.tab_buttons = []
        for idx, label, icon_name in tabs_data:
            btn = QPushButton()
            btn.setObjectName("TabBarButton")
            btn.setCheckable(True)
            btn.setIcon(qta.icon(icon_name, color="#71717a", color_active="#ffffff"))
            btn.setIconSize(QSize(16, 16))
            btn.setToolTip(label)
            if idx == 0:
                btn.setChecked(True)
            self.tab_group.addButton(btn, idx)
            tb_layout.addWidget(btn)
            self.tab_buttons.append(btn)

        self.tab_group.idClicked.connect(self._on_tab_changed)
        tb_layout.addStretch()
        main_layout.addWidget(self.tab_bar)

        # 2. Stacked Content Views
        self.content_stack = QStackedWidget(self)

        self.page_media = self._create_media_page()
        self.content_stack.addWidget(self.page_media)

        self.page_sounds = self._create_sounds_page()
        self.content_stack.addWidget(self.page_sounds)

        self.page_text = self._create_text_page()
        self.content_stack.addWidget(self.page_text)

        self.page_stickers = self._create_stickers_page()
        self.content_stack.addWidget(self.page_stickers)

        self.page_effects = self._create_effects_page()
        self.content_stack.addWidget(self.page_effects)

        self.page_transitions = self._create_transitions_page()
        self.content_stack.addWidget(self.page_transitions)

        self.page_settings = self._create_settings_page()
        self.content_stack.addWidget(self.page_settings)

        main_layout.addWidget(self.content_stack, 1)

    def _on_tab_changed(self, tab_id: int):
        self.content_stack.setCurrentIndex(tab_id)

    # =========================================================================
    # PAGE 0: MEDIA (OpenCut MediaView)
    # =========================================================================
    def _create_media_page(self) -> QWidget:
        view = QWidget()
        v_layout = QVBoxLayout(view)
        v_layout.setContentsMargins(14, 12, 14, 12)
        v_layout.setSpacing(12)

        header_row = QHBoxLayout()
        lbl_title = QLabel("Assets")
        lbl_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #ffffff;")
        header_row.addWidget(lbl_title)
        header_row.addStretch()

        btn_import = QPushButton("Import")
        btn_import.setIcon(qta.icon("fa5s.cloud-upload-alt", color="#e4e4e7"))
        btn_import.setIconSize(QSize(12, 12))
        btn_import.setStyleSheet("""
            QPushButton {
                background-color: #18181b;
                border: 1px solid #27272a;
                border-radius: 4px;
                padding: 4px 10px;
                font-weight: 500;
                color: #f4f4f5;
            }
            QPushButton:hover {
                background-color: #27272a;
            }
        """)
        btn_import.clicked.connect(self._open_import_dialog)
        header_row.addWidget(btn_import)
        v_layout.addLayout(header_row)

        self.dropzone = QFrame()
        self.dropzone.setObjectName("MediaDropzone")
        self.dropzone.setCursor(Qt.CursorShape.PointingHandCursor)
        dz_layout = QVBoxLayout(self.dropzone)
        dz_layout.setContentsMargins(16, 20, 16, 20)
        dz_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dz_layout.setSpacing(8)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon("fa5s.cloud-upload-alt", color="#71717a").pixmap(30, 30))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dz_layout.addWidget(icon_lbl)

        lbl_dz_text = QLabel("Drag and drop media files here")
        lbl_dz_text.setStyleSheet("color: #71717a; font-size: 11px;")
        lbl_dz_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dz_layout.addWidget(lbl_dz_text)

        self.dropzone.mousePressEvent = lambda e: self._open_import_dialog()
        v_layout.addWidget(self.dropzone)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("background-color: transparent; border: none;")
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        v_layout.addWidget(self.list_widget, 1)

        return view

    # =========================================================================
    # PAGE 1: SOUNDS (OpenCut SoundsView)
    # =========================================================================
    def _create_sounds_page(self) -> QWidget:
        view = QWidget()
        v_layout = QVBoxLayout(view)
        v_layout.setContentsMargins(14, 12, 14, 12)
        v_layout.setSpacing(10)

        header_row = QHBoxLayout()
        lbl_title = QLabel("Sounds")
        lbl_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #ffffff;")
        header_row.addWidget(lbl_title)
        header_row.addStretch()

        btn_imp = QPushButton("Import Audio")
        btn_imp.setStyleSheet("""
            QPushButton {
                background-color: #18181b;
                border: 1px solid #27272a;
                border-radius: 4px;
                padding: 4px 8px;
                color: #e4e4e7;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #27272a;
            }
        """)
        btn_imp.clicked.connect(self._open_import_dialog)
        header_row.addWidget(btn_imp)
        v_layout.addLayout(header_row)

        lbl_desc = QLabel("Add audio tracks or import local sound files.")
        lbl_desc.setStyleSheet("color: #71717a; font-size: 11px;")
        v_layout.addWidget(lbl_desc)

        # Audio drop area / import button
        sound_box = QFrame()
        sound_box.setStyleSheet("background-color: transparent; border: 1px dashed #26262b; border-radius: 6px; padding: 24px;")
        sb_layout = QVBoxLayout(sound_box)
        sb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sb_layout.setSpacing(8)

        icon_s = QLabel()
        icon_s.setPixmap(qta.icon("fa5s.music", color="#71717a").pixmap(28, 28))
        icon_s.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sb_layout.addWidget(icon_s)

        lbl_s_info = QLabel("Click to select an audio file (*.mp3, *.wav, *.aac)")
        lbl_s_info.setStyleSheet("color: #71717a; font-size: 11px;")
        lbl_s_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sb_layout.addWidget(lbl_s_info)

        sound_box.setCursor(Qt.CursorShape.PointingHandCursor)
        sound_box.mousePressEvent = lambda e: self._open_import_dialog()
        v_layout.addWidget(sound_box)

        v_layout.addStretch()
        return view

    # =========================================================================
    # PAGE 2: TEXT (OpenCut TextView - Exactly matching text/components/assets-view.tsx)
    # =========================================================================
    def _create_text_page(self) -> QWidget:
        view = QWidget()
        v_layout = QVBoxLayout(view)
        v_layout.setContentsMargins(14, 12, 14, 12)
        v_layout.setSpacing(12)

        lbl_title = QLabel("Text")
        lbl_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #ffffff;")
        v_layout.addWidget(lbl_title)

        # OpenCut Default Text Item (matching buildTextElement)
        card = QWidget()
        card.setFixedSize(110, 110)
        card.setStyleSheet("""
            QWidget {
                background-color: #141417;
                border: 1px solid #1f1f24;
                border-radius: 6px;
            }
            QWidget:hover {
                background-color: #1c1c21;
                border-color: #009dff;
            }
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_layout.setSpacing(6)

        lbl_icon = QLabel()
        lbl_icon.setPixmap(qta.icon("fa5s.font", color="#ffffff").pixmap(24, 24))
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_layout.addWidget(lbl_icon)

        lbl_text = QLabel("Default text")
        lbl_text.setStyleSheet("color: #f4f4f5; font-size: 11px; font-weight: 500;")
        lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_layout.addWidget(lbl_text)

        card.setCursor(Qt.CursorShape.PointingHandCursor)

        def add_default_text():
            props = ClipProperties(
                text_content="Default text",
                font_family="Segoe UI",
                font_size=56,
                font_color="#ffffff",
                font_bold=True,
                bg_pill=False,
                alignment="center"
            )
            clip = Clip(media_type="text", duration=3.0, name="Default text", properties=props)
            self.clip_add_requested.emit(clip)

        card.mousePressEvent = lambda e: add_default_text()
        v_layout.addWidget(card)

        v_layout.addStretch()
        return view

    # =========================================================================
    # PAGE 3: STICKERS (OpenCut StickersView)
    # =========================================================================
    def _create_stickers_page(self) -> QWidget:
        view = QWidget()
        v_layout = QVBoxLayout(view)
        v_layout.setContentsMargins(14, 12, 14, 12)
        v_layout.setSpacing(10)

        lbl_title = QLabel("Stickers")
        lbl_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #ffffff;")
        v_layout.addWidget(lbl_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        grid = QGridLayout(content)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(6)

        emojis = [
            "🔥", "🚀", "⭐", "👍", "❤️", "🎉",
            "💡", "⚠️", "🎯", "⚡", "💯", "✨"
        ]

        for i, emoji in enumerate(emojis):
            btn = QPushButton(emoji)
            btn.setFixedSize(52, 48)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 4px;
                    font-size: 22px;
                }
                QPushButton:hover {
                    background-color: #18181c;
                }
            """)

            def make_handler(e=emoji):
                def handler():
                    props = ClipProperties(sticker_content=e, sticker_size=80)
                    clip = Clip(media_type="sticker", duration=3.0, name=f"Sticker {e}", properties=props)
                    self.clip_add_requested.emit(clip)
                return handler

            btn.clicked.connect(make_handler(emoji))
            grid.addWidget(btn, i // 4, i % 4)

        scroll.setWidget(content)
        v_layout.addWidget(scroll, 1)
        return view

    # =========================================================================
    # PAGE 4: EFFECTS (OpenCut EffectsView)
    # =========================================================================
    def _create_effects_page(self) -> QWidget:
        view = QWidget()
        v_layout = QVBoxLayout(view)
        v_layout.setContentsMargins(14, 12, 14, 12)
        v_layout.setSpacing(10)

        lbl_title = QLabel("Effects")
        lbl_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #ffffff;")
        v_layout.addWidget(lbl_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(4)

        effects = [
            ("Normal", "none"),
            ("Black & White", "grayscale"),
            ("Warm", "warm"),
            ("Cool", "cool"),
            ("Sepia", "sepia"),
            ("Invert", "invert"),
            ("High Contrast", "high_contrast"),
        ]

        for label, filter_id in effects:
            row = QWidget()
            row.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                    border: none;
                    border-radius: 4px;
                }
                QWidget:hover {
                    background-color: #16161a;
                }
            """)
            h_layout = QHBoxLayout(row)
            h_layout.setContentsMargins(8, 6, 8, 6)

            lbl = QLabel(label)
            lbl.setStyleSheet("color: #f4f4f5; font-size: 11px;")
            h_layout.addWidget(lbl, 1)

            btn_apply = QPushButton("Apply")
            btn_apply.setStyleSheet("""
                QPushButton {
                    background-color: #1f1f24;
                    border: none;
                    border-radius: 3px;
                    padding: 3px 8px;
                    color: #e4e4e7;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #009dff;
                    color: #ffffff;
                }
            """)
            btn_apply.clicked.connect(lambda checked, fid=filter_id: self.filter_apply_requested.emit(fid))
            h_layout.addWidget(btn_apply)

            c_layout.addWidget(row)

        c_layout.addStretch()
        scroll.setWidget(content)
        v_layout.addWidget(scroll, 1)
        return view

    # =========================================================================
    # PAGE 5: TRANSITIONS (OpenCut TransitionsView)
    # =========================================================================
    def _create_transitions_page(self) -> QWidget:
        view = QWidget()
        v_layout = QVBoxLayout(view)
        v_layout.setContentsMargins(14, 12, 14, 12)
        v_layout.setSpacing(10)

        lbl_title = QLabel("Transitions")
        lbl_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #ffffff;")
        v_layout.addWidget(lbl_title)

        lbl_coming = QLabel("Transitions view coming soon...")
        lbl_coming.setStyleSheet("color: #71717a; font-size: 11px; padding-top: 10px;")
        v_layout.addWidget(lbl_coming)

        v_layout.addStretch()
        return view

    # =========================================================================
    # PAGE 6: SETTINGS (OpenCut SettingsView)
    # =========================================================================
    def _create_settings_page(self) -> QWidget:
        view = QWidget()
        v_layout = QVBoxLayout(view)
        v_layout.setContentsMargins(14, 12, 14, 12)
        v_layout.setSpacing(12)

        lbl_title = QLabel("Settings")
        lbl_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #ffffff;")
        v_layout.addWidget(lbl_title)

        # Canvas Resolution
        lbl_ar = QLabel("CANVAS RESOLUTION")
        lbl_ar.setStyleSheet("font-size: 10px; font-weight: 700; color: #71717a; letter-spacing: 0.6px;")
        v_layout.addWidget(lbl_ar)

        self.cb_res = QComboBox()
        self.cb_res.addItems(["16:9 Landscape (1920x1080)", "9:16 TikTok / Short (1080x1920)", "1:1 Square (1080x1080)"])
        self.cb_res.currentIndexChanged.connect(self._on_settings_ui_changed)
        v_layout.addWidget(self.cb_res)

        # FPS
        lbl_fps = QLabel("FRAME RATE (FPS)")
        lbl_fps.setStyleSheet("font-size: 10px; font-weight: 700; color: #71717a; letter-spacing: 0.6px; margin-top: 6px;")
        v_layout.addWidget(lbl_fps)

        self.cb_fps = QComboBox()
        self.cb_fps.addItems(["30 fps (Standard)", "60 fps (Smooth)", "24 fps (Cinema)"])
        self.cb_fps.currentIndexChanged.connect(self._on_settings_ui_changed)
        v_layout.addWidget(self.cb_fps)

        v_layout.addStretch()
        return view

    def _on_settings_ui_changed(self):
        ar_idx = self.cb_res.currentIndex()
        fps_idx = self.cb_fps.currentIndex()
        w, h = 1920, 1080
        if ar_idx == 1:
            w, h = 1080, 1920
        elif ar_idx == 2:
            w, h = 1080, 1080

        fps = 30.0
        if fps_idx == 1:
            fps = 60.0
        elif fps_idx == 2:
            fps = 24.0

        self.settings_changed.emit({"width": w, "height": h, "fps": fps})

    def _open_import_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Media Files",
            "",
            "Media Files (*.mp4 *.mov *.mkv *.avi *.mp3 *.wav *.aac *.png *.jpg *.jpeg);;All Files (*.*)"
        )
        for f in files:
            self.add_media_file(f)

    def add_media_file(self, file_path: str):
        if not os.path.exists(file_path):
            return
        if file_path in self.imported_readers:
            return

        reader = MediaReader(file_path)
        self.imported_readers[file_path] = reader

        thumb = reader.generate_thumbnail(68, 38)
        item = QListWidgetItem(self.list_widget)
        item.setSizeHint(QSize(200, 48))
        item.setData(Qt.ItemDataRole.UserRole, file_path)

        card = MediaCardWidget(file_path, thumb, reader.info, self)
        card.add_clicked.connect(self.media_add_requested.emit)
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, card)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self.media_add_requested.emit(file_path)
