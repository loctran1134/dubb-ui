from PyQt6.QtCore import QObject, QTimer, pyqtSignal
import time
from core.models import Timeline

class PlaybackController(QObject):
    """
    Playback timekeeper for real-time video preview.
    Coordinates timing loop and emits time_changed signals.
    """
    time_changed = pyqtSignal(float)
    playback_state_changed = pyqtSignal(bool)  # True = playing, False = paused

    def __init__(self, timeline: Timeline, parent=None):
        super().__init__(parent)
        self.timeline = timeline
        self.is_playing = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._last_tick_time = 0.0

        fps = self.timeline.project.fps
        interval_ms = int(1000.0 / fps)
        self._timer.setInterval(max(15, interval_ms))

    def play(self):
        if not self.is_playing:
            self.is_playing = True
            self._last_tick_time = time.perf_counter()
            self._timer.start()
            self.playback_state_changed.emit(True)

    def pause(self):
        if self.is_playing:
            self.is_playing = False
            self._timer.stop()
            self.playback_state_changed.emit(False)

    def toggle_play(self):
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def seek(self, time_sec: float):
        clamped_time = max(0.0, min(self.timeline.duration, time_sec))
        self.timeline.playhead_time = clamped_time
        self.time_changed.emit(clamped_time)

    def step_forward(self):
        fps = self.timeline.project.fps
        self.seek(self.timeline.playhead_time + (1.0 / fps))

    def step_backward(self):
        fps = self.timeline.project.fps
        self.seek(self.timeline.playhead_time - (1.0 / fps))

    def _on_tick(self):
        now = time.perf_counter()
        dt = now - self._last_tick_time
        self._last_tick_time = now

        new_time = self.timeline.playhead_time + dt
        if new_time >= self.timeline.duration:
            # Reached end of timeline
            new_time = self.timeline.duration
            self.pause()

        self.timeline.playhead_time = new_time
        self.time_changed.emit(new_time)
