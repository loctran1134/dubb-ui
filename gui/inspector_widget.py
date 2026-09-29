from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QSpinBox,
    QScrollArea, QFrame, QStackedWidget, QPushButton, QButtonGroup,
    QLineEdit, QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import qtawesome as qta
from core.models import Clip

class EmptyView(QWidget):
    """
    OpenCut EmptyView when no timeline element is selected.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon("fa5s.cog", color="#52525b").pixmap(38, 38))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)

        title_lbl = QLabel("It's empty here")
        title_lbl.setStyleSheet("font-size: 15px; font-weight: 600; color: #f4f4f5;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        sub_lbl = QLabel("Click an element on the timeline to edit its properties")
        sub_lbl.setStyleSheet("color: #71717a; font-size: 11px; text-align: center;")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setWordWrap(True)
        layout.addWidget(sub_lbl)

class PropertiesContentView(QWidget):
    """
    OpenCut Properties parameter editor with working dynamic sub-tabs
    supporting Video, Audio, Text, Sticker, and Speed parameter controls.
    """
    property_changed = pyqtSignal()
    geometry_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_clip: Clip = None

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Sub-Tabs Column (Video, Text, Audio, Speed)
        tab_col = QWidget()
        tab_col.setStyleSheet("background-color: #09090b; border-right: 1px solid #1f1f24; min-width: 40px; max-width: 40px;")
        t_layout = QVBoxLayout(tab_col)
        t_layout.setContentsMargins(0, 6, 0, 6)
        t_layout.setSpacing(2)

        self.tab_group = QButtonGroup(self)
        self.tab_group.setExclusive(True)

        tabs = [
            (0, "Video", "fa5s.video"),
            (1, "Text", "fa5s.font"),
            (2, "Audio", "fa5s.volume-up"),
            (3, "Speed", "fa5s.tachometer-alt"),
        ]

        self.tab_buttons = {}
        for idx, label, icon_name in tabs:
            btn = QPushButton()
            btn.setObjectName("TabBarButton")
            btn.setCheckable(True)
            btn.setIcon(qta.icon(icon_name, color="#71717a", color_active="#ffffff"))
            btn.setIconSize(QSize(15, 15))
            btn.setToolTip(label)
            if idx == 0:
                btn.setChecked(True)
            self.tab_group.addButton(btn, idx)
            t_layout.addWidget(btn)
            self.tab_buttons[idx] = btn

        self.tab_btn_video = self.tab_buttons[0]
        self.tab_btn_text = self.tab_buttons[1]
        self.tab_btn_audio = self.tab_buttons[2]
        self.tab_btn_speed = self.tab_buttons[3]

        self.tab_group.idClicked.connect(self._on_tab_clicked)
        t_layout.addStretch()
        main_layout.addWidget(tab_col)

        # 2. Right Stacked Parameter Area
        right_container = QWidget()
        rc_layout = QVBoxLayout(right_container)
        rc_layout.setContentsMargins(0, 0, 0, 0)
        rc_layout.setSpacing(0)

        # Header Bar
        header_bar = QWidget()
        header_bar.setStyleSheet("background-color: #0d0d0f; border-bottom: 1px solid #1f1f24; min-height: 40px; max-height: 40px;")
        hb_layout = QHBoxLayout(header_bar)
        hb_layout.setContentsMargins(14, 0, 10, 0)
        hb_layout.setSpacing(8)

        self.lbl_title = QLabel("Element Properties")
        self.lbl_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #ffffff;")
        hb_layout.addWidget(self.lbl_title, 1)

        self.btn_reset = QPushButton()
        self.btn_reset.setObjectName("GhostIconButton")
        self.btn_reset.setIcon(qta.icon("fa5s.undo-alt", color="#71717a"))
        self.btn_reset.setIconSize(QSize(12, 12))
        self.btn_reset.setToolTip("Reset Properties")
        self.btn_reset.clicked.connect(self._reset_current_tab)
        hb_layout.addWidget(self.btn_reset)

        rc_layout.addWidget(header_bar)

        # Tab Pages Stack
        self.tab_stack = QStackedWidget()

        # Page 0: VIDEO / TRANSFORM PAGE
        self.page_video = self._create_video_page()
        self.tab_stack.addWidget(self.page_video)

        # Page 1: TEXT PAGE
        self.page_text = self._create_text_page()
        self.tab_stack.addWidget(self.page_text)

        # Page 2: AUDIO PAGE
        self.page_audio = self._create_audio_page()
        self.tab_stack.addWidget(self.page_audio)

        # Page 3: SPEED PAGE
        self.page_speed = self._create_speed_page()
        self.tab_stack.addWidget(self.page_speed)

        rc_layout.addWidget(self.tab_stack, 1)
        main_layout.addWidget(right_container, 1)

    def _create_card(self, title: str, on_reset=None) -> tuple[QWidget, QVBoxLayout]:
        card = QWidget()
        card.setStyleSheet("background-color: transparent; border: none;")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(2, 6, 2, 8)
        layout.setSpacing(8)

        header_row = QHBoxLayout()
        header = QLabel(title)
        header.setStyleSheet("font-size: 10px; font-weight: 700; color: #71717a; letter-spacing: 0.8px;")
        header_row.addWidget(header, 1)

        if on_reset:
            btn_rst = QPushButton()
            btn_rst.setObjectName("GhostIconButton")
            btn_rst.setIcon(qta.icon("fa5s.redo", color="#52525b"))
            btn_rst.setIconSize(QSize(10, 10))
            btn_rst.setToolTip(f"Reset {title}")
            btn_rst.clicked.connect(on_reset)
            header_row.addWidget(btn_rst)

        layout.addLayout(header_row)
        return card, layout

    def _add_param_row(self, parent_layout, label: str, min_val: int, max_val: int, default: int, suffix: str):
        row = QWidget()
        h_layout = QHBoxLayout(row)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(8)

        lbl = QLabel(label)
        lbl.setFixedWidth(75)
        lbl.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        h_layout.addWidget(lbl)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default)
        h_layout.addWidget(slider, 1)

        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(default)
        spin.setSuffix(suffix)
        spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        spin.setFixedWidth(64)
        h_layout.addWidget(spin)

        slider.valueChanged.connect(spin.setValue)
        spin.valueChanged.connect(slider.setValue)

        parent_layout.addWidget(row)
        return slider, spin

    # -------------------------------------------------------------------------
    # PAGE 0: VIDEO / TRANSFORM & FILTER
    # -------------------------------------------------------------------------
    def _create_video_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(12, 12, 12, 12)
        c_layout.setSpacing(12)

        # Transform Card
        sec_transform, t_layout = self._create_card("TRANSFORM", on_reset=self._reset_transform)
        self.slider_scale, self.spin_scale = self._add_param_row(t_layout, "Scale", 10, 300, 100, "%")
        self.slider_scale.valueChanged.connect(self._on_scale_changed)

        self.slider_pos_x, self.spin_pos_x = self._add_param_row(t_layout, "Position X", -1000, 1000, 0, "px")
        self.slider_pos_x.valueChanged.connect(self._on_pos_x_changed)

        self.slider_pos_y, self.spin_pos_y = self._add_param_row(t_layout, "Position Y", -1000, 1000, 0, "px")
        self.slider_pos_y.valueChanged.connect(self._on_pos_y_changed)

        self.slider_rot, self.spin_rot = self._add_param_row(t_layout, "Rotation", -180, 180, 0, "°")
        self.slider_rot.valueChanged.connect(self._on_rot_changed)
        c_layout.addWidget(sec_transform)

        # Compositing & Filter Card
        sec_blend, b_layout = self._create_card("COMPOSITING & FILTER", on_reset=self._reset_opacity)
        self.slider_opacity, self.spin_opacity = self._add_param_row(b_layout, "Opacity", 0, 100, 100, "%")
        self.slider_opacity.valueChanged.connect(self._on_opacity_changed)

        # Filter Dropdown
        row_filter = QHBoxLayout()
        lbl_f = QLabel("Filter Effect")
        lbl_f.setFixedWidth(75)
        lbl_f.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        row_filter.addWidget(lbl_f)

        self.cb_filter = QComboBox()
        self.cb_filter.addItem("None (Original)", "none")
        self.cb_filter.addItem("Black & White", "grayscale")
        self.cb_filter.addItem("Warm Golden", "warm")
        self.cb_filter.addItem("Cool Blue", "cool")
        self.cb_filter.addItem("Sepia Vintage", "sepia")
        self.cb_filter.addItem("Invert Colors", "invert")
        self.cb_filter.addItem("High Contrast", "high_contrast")
        self.cb_filter.currentIndexChanged.connect(self._on_filter_changed)
        row_filter.addWidget(self.cb_filter, 1)
        b_layout.addLayout(row_filter)

        c_layout.addWidget(sec_blend)
        c_layout.addStretch()
        scroll.setWidget(content)
        return scroll

    # -------------------------------------------------------------------------
    # PAGE 1: TEXT EDITOR
    # -------------------------------------------------------------------------
    def _create_text_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(12, 12, 12, 12)
        c_layout.setSpacing(12)

        sec_text, t_layout = self._create_card("TYPOGRAPHY CONTENT")

        # Text input
        lbl_content = QLabel("Text String")
        lbl_content.setStyleSheet("color: #a1a1aa; font-size: 10px; font-weight: 600;")
        t_layout.addWidget(lbl_content)

        self.txt_content = QLineEdit()
        self.txt_content.setStyleSheet("""
            QLineEdit {
                background-color: #18181b;
                border: 1px solid #27272a;
                border-radius: 4px;
                padding: 6px 8px;
                color: #ffffff;
                font-size: 12px;
            }
        """)
        self.txt_content.textChanged.connect(self._on_text_string_changed)
        t_layout.addWidget(self.txt_content)

        # Font Family & Size
        self.slider_font_size, self.spin_font_size = self._add_param_row(t_layout, "Font Size", 16, 144, 56, "px")
        self.slider_font_size.valueChanged.connect(self._on_font_size_changed)

        # Color & Pill options
        row_opts = QHBoxLayout()
        self.chk_bold = QCheckBox("Bold")
        self.chk_bold.setStyleSheet("color: #f4f4f5; font-size: 11px;")
        self.chk_bold.toggled.connect(self._on_bold_toggled)
        row_opts.addWidget(self.chk_bold)

        self.chk_pill = QCheckBox("Background Box")
        self.chk_pill.setStyleSheet("color: #f4f4f5; font-size: 11px;")
        self.chk_pill.toggled.connect(self._on_pill_toggled)
        row_opts.addWidget(self.chk_pill)
        row_opts.addStretch()
        t_layout.addLayout(row_opts)

        # Color presets
        row_color = QHBoxLayout()
        lbl_c = QLabel("Text Color")
        lbl_c.setFixedWidth(75)
        lbl_c.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        row_color.addWidget(lbl_c)

        colors = [("#ffffff", "White"), ("#facc15", "Yellow"), ("#009dff", "Blue"), ("#ef4444", "Red"), ("#22c55e", "Green")]
        for hex_code, name in colors:
            btn_col = QPushButton()
            btn_col.setFixedSize(18, 18)
            btn_col.setStyleSheet(f"background-color: {hex_code}; border-radius: 9px; border: 1px solid #27272a;")
            btn_col.setToolTip(name)
            btn_col.clicked.connect(lambda checked, c=hex_code: self._set_text_color(c))
            row_color.addWidget(btn_col)
        row_color.addStretch()
        t_layout.addLayout(row_color)

        c_layout.addWidget(sec_text)

        # Transform Card for text position
        sec_text_trans, tt_layout = self._create_card("POSITION & SCALE")
        self.slider_text_pos_x, _ = self._add_param_row(tt_layout, "Position X", -1000, 1000, 0, "px")
        self.slider_text_pos_x.valueChanged.connect(self._on_pos_x_changed)

        self.slider_text_pos_y, _ = self._add_param_row(tt_layout, "Position Y", -1000, 1000, 0, "px")
        self.slider_text_pos_y.valueChanged.connect(self._on_pos_y_changed)

        self.slider_text_scale, _ = self._add_param_row(tt_layout, "Scale", 10, 300, 100, "%")
        self.slider_text_scale.valueChanged.connect(self._on_scale_changed)

        c_layout.addWidget(sec_text_trans)
        c_layout.addStretch()
        scroll.setWidget(content)
        return scroll

    # -------------------------------------------------------------------------
    # PAGE 2: AUDIO
    # -------------------------------------------------------------------------
    def _create_audio_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(12, 12, 12, 12)
        c_layout.setSpacing(12)

        sec_audio, a_layout = self._create_card("AUDIO VOLUME", on_reset=self._reset_audio)
        self.slider_vol, self.spin_vol = self._add_param_row(a_layout, "Volume", 0, 200, 100, "%")
        self.slider_vol.valueChanged.connect(self._on_vol_changed)

        self.btn_mute = QPushButton("Mute Audio Track")
        self.btn_mute.setCheckable(True)
        self.btn_mute.setIcon(qta.icon("fa5s.volume-mute", color="#71717a"))
        self.btn_mute.setStyleSheet("""
            QPushButton {
                background-color: #18181b;
                border: 1px solid #27272a;
                border-radius: 4px;
                padding: 6px;
                color: #e4e4e7;
                font-size: 11px;
            }
            QPushButton:checked {
                background-color: #ef4444;
                color: #ffffff;
                border-color: #dc2626;
            }
        """)
        self.btn_mute.toggled.connect(self._on_mute_toggled)
        a_layout.addWidget(self.btn_mute)
        c_layout.addWidget(sec_audio)

        c_layout.addStretch()
        scroll.setWidget(content)
        return scroll

    # -------------------------------------------------------------------------
    # PAGE 3: SPEED
    # -------------------------------------------------------------------------
    def _create_speed_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(12, 12, 12, 12)
        c_layout.setSpacing(12)

        sec_speed, s_layout = self._create_card("PLAYBACK SPEED", on_reset=self._reset_speed)
        self.slider_speed, self.spin_speed = self._add_param_row(s_layout, "Speed", 25, 400, 100, "%")
        self.slider_speed.valueChanged.connect(self._on_speed_changed)

        # Speed Presets
        presets_row = QHBoxLayout()
        presets = [("0.5x", 50), ("1.0x", 100), ("1.5x", 150), ("2.0x", 200)]
        for label, val in presets:
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #18181b;
                    border: 1px solid #27272a;
                    border-radius: 4px;
                    padding: 4px 6px;
                    color: #d4d4d8;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #27272a;
                    color: #ffffff;
                }
            """)
            btn.clicked.connect(lambda checked, v=val: self.slider_speed.setValue(v))
            presets_row.addWidget(btn)
        s_layout.addLayout(presets_row)

        self.lbl_speed_duration = QLabel("Duration: 0.0s")
        self.lbl_speed_duration.setStyleSheet("color: #71717a; font-size: 10px;")
        s_layout.addWidget(self.lbl_speed_duration)

        c_layout.addWidget(sec_speed)
        c_layout.addStretch()
        scroll.setWidget(content)
        return scroll

    def _on_tab_clicked(self, tab_id: int):
        self.tab_stack.setCurrentIndex(tab_id)

    def _reset_current_tab(self):
        cur = self.tab_stack.currentIndex()
        if cur == 0:
            self._reset_transform()
            self._reset_opacity()
        elif cur == 1:
            if self.current_clip and self.current_clip.media_type == "text":
                self.slider_font_size.setValue(56)
                self.chk_bold.setChecked(True)
                self.chk_pill.setChecked(False)
        elif cur == 2:
            self._reset_audio()
        elif cur == 3:
            self._reset_speed()

    def _reset_transform(self):
        self.slider_scale.setValue(100)
        self.slider_pos_x.setValue(0)
        self.slider_pos_y.setValue(0)
        self.slider_rot.setValue(0)

    def _reset_opacity(self):
        self.slider_opacity.setValue(100)
        self.cb_filter.setCurrentIndex(0)

    def _reset_audio(self):
        self.slider_vol.setValue(100)
        self.btn_mute.setChecked(False)

    def _reset_speed(self):
        self.slider_speed.setValue(100)

    def inspect_clip(self, clip: Clip):
        self.current_clip = clip
        if not clip:
            return

        self.lbl_title.setText(clip.name)
        p = clip.properties

        # Adapt sub-tabs by clip type
        if clip.media_type == "text":
            self.tab_btn_video.setVisible(False)
            self.tab_btn_text.setVisible(True)
            self.tab_btn_audio.setVisible(False)
            self.tab_btn_speed.setVisible(True)

            self.tab_btn_text.setChecked(True)
            self.tab_stack.setCurrentIndex(1)

            self.txt_content.blockSignals(True)
            self.txt_content.setText(p.text_content)
            self.txt_content.blockSignals(False)

            self.slider_font_size.blockSignals(True)
            self.slider_font_size.setValue(p.font_size)
            self.slider_font_size.blockSignals(False)
            self.spin_font_size.setValue(p.font_size)

            self.chk_bold.blockSignals(True)
            self.chk_bold.setChecked(p.font_bold)
            self.chk_bold.blockSignals(False)

            self.chk_pill.blockSignals(True)
            self.chk_pill.setChecked(p.bg_pill)
            self.chk_pill.blockSignals(False)

            self.slider_text_pos_x.blockSignals(True)
            self.slider_text_pos_x.setValue(int(p.pos_x))
            self.slider_text_pos_x.blockSignals(False)

            self.slider_text_pos_y.blockSignals(True)
            self.slider_text_pos_y.setValue(int(p.pos_y))
            self.slider_text_pos_y.blockSignals(False)

            self.slider_text_scale.blockSignals(True)
            self.slider_text_scale.setValue(int(p.scale_x * 100))
            self.slider_text_scale.blockSignals(False)

        elif clip.media_type == "audio":
            self.tab_btn_video.setVisible(False)
            self.tab_btn_text.setVisible(False)
            self.tab_btn_audio.setVisible(True)
            self.tab_btn_speed.setVisible(True)

            self.tab_btn_audio.setChecked(True)
            self.tab_stack.setCurrentIndex(2)

        else:  # video / sticker / other
            self.tab_btn_video.setVisible(True)
            self.tab_btn_text.setVisible(False)
            self.tab_btn_audio.setVisible(True)
            self.tab_btn_speed.setVisible(True)

            self.tab_btn_video.setChecked(True)
            self.tab_stack.setCurrentIndex(0)

        # Video/Transform Fields
        self.slider_scale.blockSignals(True)
        self.slider_scale.setValue(int(round(p.scale_x * 100)))
        self.slider_scale.blockSignals(False)
        self.spin_scale.setValue(int(round(p.scale_x * 100)))

        self.slider_pos_x.blockSignals(True)
        self.slider_pos_x.setValue(int(round(p.pos_x)))
        self.slider_pos_x.blockSignals(False)
        self.spin_pos_x.setValue(int(round(p.pos_x)))

        self.slider_pos_y.blockSignals(True)
        self.slider_pos_y.setValue(int(round(p.pos_y)))
        self.slider_pos_y.blockSignals(False)
        self.spin_pos_y.setValue(int(round(p.pos_y)))

        self.slider_rot.blockSignals(True)
        self.slider_rot.setValue(int(round(p.rotation)))
        self.slider_rot.blockSignals(False)
        self.spin_rot.setValue(int(round(p.rotation)))

        self.slider_opacity.blockSignals(True)
        self.slider_opacity.setValue(int(round(p.opacity * 100)))
        self.slider_opacity.blockSignals(False)
        self.spin_opacity.setValue(int(round(p.opacity * 100)))

        # Filter combo
        self.cb_filter.blockSignals(True)
        idx = self.cb_filter.findData(p.filter_type)
        if idx >= 0:
            self.cb_filter.setCurrentIndex(idx)
        else:
            self.cb_filter.setCurrentIndex(0)
        self.cb_filter.blockSignals(False)

        # Audio Fields
        self.slider_vol.blockSignals(True)
        self.slider_vol.setValue(int(round(p.volume * 100)))
        self.slider_vol.blockSignals(False)
        self.spin_vol.setValue(int(round(p.volume * 100)))
        self.btn_mute.setChecked(p.volume == 0.0)

        # Speed Fields
        self.slider_speed.blockSignals(True)
        self.slider_speed.setValue(int(round(p.speed * 100)))
        self.slider_speed.blockSignals(False)
        self.spin_speed.setValue(int(round(p.speed * 100)))
        self._update_speed_label()

    def _update_speed_label(self):
        if self.current_clip:
            dur = self.current_clip.duration
            orig_dur = max(0.1, self.current_clip.source_out - self.current_clip.source_in)
            self.lbl_speed_duration.setText(f"Original: {orig_dur:.2f}s  →  Timeline: {dur:.2f}s")

    def _on_scale_changed(self, val: int):
        if self.current_clip:
            self.current_clip.properties.scale_x = val / 100.0
            self.current_clip.properties.scale_y = val / 100.0
            self.property_changed.emit()

    def _on_pos_x_changed(self, val: int):
        if self.current_clip:
            self.current_clip.properties.pos_x = float(val)
            self.property_changed.emit()

    def _on_pos_y_changed(self, val: int):
        if self.current_clip:
            self.current_clip.properties.pos_y = float(val)
            self.property_changed.emit()

    def _on_rot_changed(self, val: int):
        if self.current_clip:
            self.current_clip.properties.rotation = float(val)
            self.property_changed.emit()

    def _on_opacity_changed(self, val: int):
        if self.current_clip:
            self.current_clip.properties.opacity = val / 100.0
            self.property_changed.emit()

    def _on_filter_changed(self, idx: int):
        if self.current_clip:
            filter_id = self.cb_filter.currentData()
            self.current_clip.properties.filter_type = filter_id
            self.property_changed.emit()

    def _on_vol_changed(self, val: int):
        if self.current_clip:
            self.current_clip.properties.volume = val / 100.0
            self.btn_mute.setChecked(val == 0)
            self.property_changed.emit()

    def _on_mute_toggled(self, checked: bool):
        if self.current_clip:
            if checked:
                self.slider_vol.setValue(0)
            elif self.slider_vol.value() == 0:
                self.slider_vol.setValue(100)

    def _on_speed_changed(self, val: int):
        if self.current_clip:
            new_speed = max(0.1, val / 100.0)
            self.current_clip.properties.speed = new_speed
            source_span = max(0.1, self.current_clip.source_out - self.current_clip.source_in)
            self.current_clip.duration = source_span / new_speed
            self._update_speed_label()
            self.geometry_changed.emit()
            self.property_changed.emit()

    def _on_text_string_changed(self, text: str):
        if self.current_clip and self.current_clip.media_type == "text":
            self.current_clip.properties.text_content = text
            self.current_clip.name = f"Text: {text[:15]}" if text else "Text Element"
            self.lbl_title.setText(self.current_clip.name)
            self.property_changed.emit()
            self.geometry_changed.emit()

    def _on_font_size_changed(self, val: int):
        if self.current_clip and self.current_clip.media_type == "text":
            self.current_clip.properties.font_size = val
            self.property_changed.emit()

    def _on_bold_toggled(self, checked: bool):
        if self.current_clip and self.current_clip.media_type == "text":
            self.current_clip.properties.font_bold = checked
            self.property_changed.emit()

    def _on_pill_toggled(self, checked: bool):
        if self.current_clip and self.current_clip.media_type == "text":
            self.current_clip.properties.bg_pill = checked
            self.property_changed.emit()

    def _set_text_color(self, hex_color: str):
        if self.current_clip and self.current_clip.media_type == "text":
            self.current_clip.properties.font_color = hex_color
            self.property_changed.emit()

class InspectorWidget(QWidget):
    """
    OpenCut PropertiesPanel.
    Shows EmptyView when no element is selected, and PropertiesContentView when an element is active.
    """
    property_changed = pyqtSignal()
    geometry_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("OpenCutPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.empty_view = EmptyView(self)
        self.content_view = PropertiesContentView(self)
        self.content_view.property_changed.connect(self.property_changed.emit)
        self.content_view.geometry_changed.connect(self.geometry_changed.emit)

        self.stack.addWidget(self.empty_view)
        self.stack.addWidget(self.content_view)

        layout.addWidget(self.stack)
        self.stack.setCurrentIndex(0)

    def inspect_clip(self, clip: Clip):
        if clip is None:
            self.stack.setCurrentIndex(0)
        else:
            self.content_view.inspect_clip(clip)
            self.stack.setCurrentIndex(1)
