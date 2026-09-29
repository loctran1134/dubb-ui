import subprocess
import os
import tempfile
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage
from core.models import Timeline
from engine.compositor import Compositor

class ExportWorker(QThread):
    """
    Background worker thread that renders timeline frames and pipes them directly into native FFmpeg.
    Avoids pipe deadlock by redirecting stderr to a log file.
    """
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, timeline: Timeline, output_path: str, ffmpeg_bin: str = "ffmpeg"):
        super().__init__()
        self.timeline = timeline
        self.output_path = output_path
        self.ffmpeg_bin = ffmpeg_bin
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        proj = self.timeline.project
        fps = proj.fps
        duration = self.timeline.duration
        total_frames = max(1, int(duration * fps))

        compositor = Compositor(self.timeline)

        cmd = [
            self.ffmpeg_bin,
            "-y",  # Overwrite
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{proj.width}x{proj.height}",
            "-pix_fmt", "rgb24",
            "-r", str(fps),
            "-i", "-",  # Read from stdin
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            self.output_path
        ]

        proc = None
        log_file = None
        try:
            # Hide console window on Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            log_file = tempfile.TemporaryFile(mode='w+b')

            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=log_file,
                startupinfo=startupinfo
            )

            for frame_idx in range(total_frames):
                if self._is_cancelled:
                    proc.kill()
                    self.error.emit("Export cancelled by user.")
                    return

                t = frame_idx / fps
                qimg = compositor.render_frame(t)

                # Convert QImage to raw RGB24 bytes
                rgb_img = qimg.convertToFormat(QImage.Format.Format_RGB888)
                ptr = rgb_img.bits()
                ptr.setsize(rgb_img.sizeInBytes())
                raw_bytes = bytes(ptr)

                proc.stdin.write(raw_bytes)

                percent = int((frame_idx + 1) * 100 / total_frames)
                self.progress.emit(percent)

            proc.stdin.close()
            proc.wait()

            if proc.returncode == 0:
                self.finished.emit(self.output_path)
            else:
                log_file.seek(0)
                stderr_output = log_file.read().decode('utf-8', errors='ignore')
                self.error.emit(f"FFmpeg error (code {proc.returncode}): {stderr_output[-400:]}")

        except Exception as e:
            if proc:
                try:
                    proc.kill()
                except Exception:
                    pass
            self.error.emit(f"Export exception: {str(e)}")
        finally:
            if log_file:
                try:
                    log_file.close()
                except Exception:
                    pass
            compositor.cleanup()
