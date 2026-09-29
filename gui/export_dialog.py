import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QProgressBar, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from core.models import Timeline
from export.exporter import ExportWorker

class ExportDialog(QDialog):
    """
    Export modal dialog to render and export the final video via FFmpeg.
    """
    def __init__(self, timeline: Timeline, parent=None):
        super().__init__(parent)
        self.timeline = timeline
        self.worker: ExportWorker = None

        self.setWindowTitle("Export Video")
        self.setFixedSize(480, 240)
        self.setStyleSheet("background-color: #17171e; color: #f1f5f9;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header info
        proj = self.timeline.project
        lbl_info = QLabel(f"Export Format: MP4 (H.264 / AAC) • {proj.width}x{proj.height} @ {int(proj.fps)}fps")
        lbl_info.setStyleSheet("color: #a78bfa; font-weight: 600; font-size: 13px;")
        layout.addWidget(lbl_info)

        # Output path selection
        path_layout = QHBoxLayout()
        default_dir = os.path.expanduser("~\\Videos")
        if not os.path.exists(default_dir):
            default_dir = os.getcwd()
        default_path = os.path.join(default_dir, "export_output.mp4")

        self.txt_path = QLineEdit(default_path)
        path_layout.addWidget(self.txt_path, 1)

        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._browse)
        path_layout.addWidget(btn_browse)
        layout.addLayout(path_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1f1f28;
                border: 1px solid #2d2d3a;
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #7c3aed;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Status label
        self.lbl_status = QLabel("Ready to export.")
        self.lbl_status.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(self.lbl_status)

        # Action buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self._on_cancel)
        btn_box.addWidget(self.btn_cancel)

        self.btn_export = QPushButton("Export Now")
        self.btn_export.setObjectName("PrimaryButton")
        self.btn_export.clicked.connect(self._start_export)
        btn_box.addWidget(self.btn_export)

        layout.addLayout(btn_box)

    def _browse(self):
        dest, _ = QFileDialog.getSaveFileName(
            self, "Save Export Video", self.txt_path.text(), "MP4 Video (*.mp4)"
        )
        if dest:
            self.txt_path.setText(dest)

    def _start_export(self):
        output_file = self.txt_path.text().strip()
        if not output_file:
            QMessageBox.warning(self, "Invalid Path", "Please specify a valid export file path.")
            return

        self.btn_export.setEnabled(False)
        self.btn_cancel.setText("Abort")
        self.lbl_status.setText("Rendering video frames and encoding with FFmpeg...")

        self.worker = ExportWorker(self.timeline, output_file)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, val: int):
        self.progress_bar.setValue(val)
        self.lbl_status.setText(f"Encoding: {val}%")

    def _on_finished(self, out_path: str):
        self.progress_bar.setValue(100)
        self.lbl_status.setText(f"Export completed: {out_path}")
        self.btn_cancel.setText("Close")
        QMessageBox.information(self, "Success", f"Video successfully exported to:\n{out_path}")
        self.accept()

    def _on_error(self, err_msg: str):
        self.btn_export.setEnabled(True)
        self.btn_cancel.setText("Cancel")
        self.lbl_status.setText("Export failed.")
        QMessageBox.critical(self, "Export Error", err_msg)

    def _on_cancel(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
        self.reject()
