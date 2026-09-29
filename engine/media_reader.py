import av
import numpy as np
from PyQt6.QtGui import QImage, QPixmap
from typing import Optional, Dict
import os

class MediaInfo:
    def __init__(self, path: str):
        self.path = path
        self.filename = os.path.basename(path)
        self.width = 1920
        self.height = 1080
        self.duration = 0.0
        self.fps = 30.0
        self.has_video = False
        self.has_audio = False
        self.codec = ""
        self._read_info()

    def _read_info(self):
        try:
            with av.open(self.path) as container:
                if len(container.streams.video) > 0:
                    v = container.streams.video[0]
                    self.has_video = True
                    self.width = v.codec_context.width or 1920
                    self.height = v.codec_context.height or 1080
                    self.codec = v.codec_context.name
                    if v.duration and v.time_base:
                        self.duration = float(v.duration * v.time_base)
                    elif container.duration:
                        self.duration = float(container.duration / av.time_base)
                    if v.average_rate:
                        self.fps = float(v.average_rate)
                    elif v.base_rate:
                        self.fps = float(v.base_rate)

                if len(container.streams.audio) > 0:
                    self.has_audio = True
                    if not self.has_video and container.duration:
                        self.duration = float(container.duration / av.time_base)
        except Exception as e:
            print(f"Error inspecting media {self.path}: {e}")

class MediaReader:
    """
    High-performance native media reader using PyAV (FFmpeg bindings).
    Features smart forward-streaming (avoiding redundant seek resets) + LRU cache.
    """
    def __init__(self, path: str):
        self.path = path
        self.info = MediaInfo(path)
        self._container = None
        self._video_stream = None
        self._current_time = -1.0
        self._frame_cache: Dict[int, QImage] = {}
        self._max_cache_size = 100
        self._decoder_gen = None

    def open(self):
        if self._container is None and self.info.has_video:
            try:
                self._container = av.open(self.path)
                if len(self._container.streams.video) > 0:
                    self._video_stream = self._container.streams.video[0]
                    self._video_stream.thread_type = "AUTO"
                    self._decoder_gen = self._container.decode(self._video_stream)
                    self._current_time = 0.0
            except Exception as e:
                print(f"Failed to open media stream {self.path}: {e}")

    def close(self):
        if self._container is not None:
            try:
                self._container.close()
            except Exception:
                pass
            self._container = None
            self._video_stream = None
            self._decoder_gen = None
            self._current_time = -1.0

    def _frame_to_qimage(self, frame) -> QImage:
        img_rgb = frame.to_rgb()
        arr = img_rgb.to_ndarray()
        h, w, ch = arr.shape
        bytes_per_line = ch * w
        return QImage(arr.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()

    def get_frame_at_time(self, time_sec: float) -> Optional[QImage]:
        if not self.info.has_video:
            return None

        time_sec = max(0.0, min(self.info.duration, time_sec))
        frame_idx = int(round(time_sec * self.info.fps))
        if frame_idx in self._frame_cache:
            return self._frame_cache[frame_idx]

        self.open()
        if self._container is None or self._video_stream is None:
            return None

        tb = self._video_stream.time_base
        half_frame = 0.5 / max(1.0, self.info.fps)

        try:
            # Check if we can just read forward (crucial for smooth playback & fast export!)
            can_advance = (
                self._decoder_gen is not None and
                self._current_time <= time_sec and
                (time_sec - self._current_time) < 0.5
            )

            if not can_advance:
                # Seek to target
                target_pts = int(time_sec / tb)
                self._container.seek(target_pts, stream=self._video_stream, backward=True)
                self._decoder_gen = self._container.decode(self._video_stream)

            # Pull frames from generator until reaching target time
            last_qimg = None
            for frame in self._decoder_gen:
                if frame.pts is not None:
                    self._current_time = float(frame.pts * tb)
                else:
                    self._current_time += 1.0 / self.info.fps

                last_qimg = self._frame_to_qimage(frame)
                cur_idx = int(round(self._current_time * self.info.fps))
                if len(self._frame_cache) < self._max_cache_size:
                    self._frame_cache[cur_idx] = last_qimg

                if self._current_time >= time_sec - half_frame:
                    break

            if last_qimg is not None:
                self._frame_cache[frame_idx] = last_qimg
                return last_qimg

        except (av.AVError, StopIteration) as e:
            # If stream reached end, restart generator
            try:
                self._container.seek(0, stream=self._video_stream)
                self._decoder_gen = self._container.decode(self._video_stream)
                self._current_time = 0.0
            except Exception:
                pass

        return None

    def generate_thumbnail(self, width: int = 160, height: int = 90) -> QPixmap:
        frame = self.get_frame_at_time(min(0.5, self.info.duration * 0.1))
        if frame is not None:
            pix = QPixmap.fromImage(frame)
            return pix.scaled(width, height)
        blank = QPixmap(width, height)
        blank.fill()
        return blank
