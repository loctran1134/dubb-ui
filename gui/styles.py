"""
OpenCut Design System tokens & stylesheet.
Exact palette, typography and component aesthetics from OpenCut.
"""

OPENCUT_THEME_QSS = """
/* Global Application Reset */
QWidget {
    background-color: #09090b;
    color: #e4e4e7;
    font-family: "Segoe UI", "Inter", -apple-system, sans-serif;
    font-size: 12px;
    border: none;
    outline: none;
}

QMainWindow {
    background-color: #09090b;
}

/* OpenCut Header (EditorHeader: h-[3.4rem] border-b) */
#EditorHeader {
    background-color: #09090b;
    border-bottom: 1px solid #1f1f24;
    min-height: 46px;
    max-height: 46px;
    padding: 0px 14px;
}

#LogoText {
    font-size: 15px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.4px;
}

/* Editable Project Name */
#EditableProjectName {
    background-color: transparent;
    color: #e4e4e7;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 13px;
    font-weight: 500;
}
#EditableProjectName:hover {
    background-color: #18181b;
    border: 1px solid #27272a;
}
#EditableProjectName:focus {
    background-color: #121215;
    border: 1px solid #009dff;
}

/* Panels (OpenCut flat panel surface with seamless 1px hairline dividers) */
#OpenCutPanel {
    background-color: #09090b;
    border: none;
}

/* Left TabBar (OpenCut TabBar: 44px width, vertical icon stack) */
#AssetsTabBar {
    background-color: #09090b;
    border-right: 1px solid #18181b;
    min-width: 44px;
    max-width: 44px;
}

QPushButton#TabBarButton {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 8px 0px;
    color: #71717a;
}
QPushButton#TabBarButton:hover {
    background-color: #18181b;
    color: #f4f4f5;
}
QPushButton#TabBarButton:checked {
    background-color: #27272a;
    color: #009dff;
}

/* Primary Export Button (OpenCut primary blue #009dff) */
QPushButton#ExportButton {
    background-color: #009dff;
    color: #ffffff;
    border: 1px solid #008ae0;
    border-radius: 4px;
    padding: 5px 16px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton#ExportButton:hover {
    background-color: #008be3;
}
QPushButton#ExportButton:pressed {
    background-color: #0077c2;
}

/* Ghost / Icon Tool Buttons */
QPushButton#GhostIconButton {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 5px 6px;
    color: #a1a1aa;
}
QPushButton#GhostIconButton:hover {
    background-color: #18181b;
    color: #ffffff;
}
QPushButton#GhostIconButton:checked {
    background-color: #27272a;
    color: #009dff;
}

/* Upload Dropzone (OpenCut MediaDragOverlay) */
#MediaDropzone {
    background-color: rgba(255, 255, 255, 0.012);
    border: 1px dashed #26262b;
    border-radius: 6px;
    padding: 20px 16px;
}
#MediaDropzone:hover {
    background-color: rgba(255, 255, 255, 0.035);
    border-color: #009dff;
}

/* Sliders (OpenCut Custom Slider) */
QSlider::groove:horizontal {
    height: 4px;
    background: #27272a;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: #009dff;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #ffffff;
    border: 1px solid #009dff;
    width: 12px;
    margin-top: -4px;
    margin-bottom: -4px;
    border-radius: 6px;
}
QSlider::handle:horizontal:hover {
    background: #bae6fd;
}

/* SpinBoxes & Inputs */
QSpinBox, QDoubleSpinBox, QLineEdit, QComboBox {
    background-color: #141417;
    border: 1px solid #1f1f24;
    border-radius: 4px;
    padding: 3px 6px;
    color: #f4f4f5;
    font-size: 11px;
}
QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus, QComboBox:focus {
    border: 1px solid #009dff;
}
QSpinBox::up-button, QDoubleSpinBox::up-button {
    width: 14px;
    background: #18181b;
    border: none;
    border-top-right-radius: 3px;
}
QSpinBox::down-button, QDoubleSpinBox::down-button {
    width: 14px;
    background: #18181b;
    border: none;
    border-bottom-right-radius: 3px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background: #27272a;
}
QComboBox::drop-down {
    border: none;
}

/* Splitters (Clean 1px hairline) */
QSplitter::handle {
    background-color: #18181b;
}
QSplitter::handle:hover {
    background-color: #009dff;
}
QSplitter::handle:horizontal {
    width: 1px;
}
QSplitter::handle:vertical {
    height: 1px;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 5px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #27272a;
    min-height: 20px;
    border-radius: 2px;
}
QScrollBar::handle:vertical:hover {
    background: #3f3f46;
}
QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 5px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: #27272a;
    min-width: 20px;
    border-radius: 2px;
}
QScrollBar::handle:horizontal:hover {
    background: #3f3f46;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
    height: 0px;
}
"""
