import math

class Timecode:
    """
    Utility class for timecode conversions between frames, seconds, and SMPTE formatted strings.
    """
    def __init__(self, fps: float = 30.0):
        self.fps = max(1.0, float(fps))

    def seconds_to_frames(self, seconds: float) -> int:
        return max(0, int(round(seconds * self.fps)))

    def frames_to_seconds(self, frames: int) -> float:
        return max(0.0, frames / self.fps)

    def format_time(self, seconds: float) -> str:
        """
        Formats seconds into HH:MM:SS:FF string.
        """
        if seconds < 0:
            seconds = 0.0
        total_frames = self.seconds_to_frames(seconds)
        frames = total_frames % int(self.fps)
        total_secs = int(seconds)
        secs = total_secs % 60
        mins = (total_secs // 60) % 60
        hours = total_secs // 3600
        return f"{hours:02d}:{mins:02d}:{secs:02d}:{frames:02d}"

    def format_short_time(self, seconds: float) -> str:
        """
        Formats seconds into MM:SS.ff string for ruler display.
        """
        if seconds < 0:
            seconds = 0.0
        total_secs = int(seconds)
        fraction = int((seconds - total_secs) * 100)
        secs = total_secs % 60
        mins = total_secs // 60
        return f"{mins:02d}:{secs:02d}.{fraction:02d}"
