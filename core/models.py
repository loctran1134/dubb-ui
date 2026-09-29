import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import os

@dataclass
class ClipProperties:
    scale_x: float = 1.0
    scale_y: float = 1.0
    pos_x: float = 0.0
    pos_y: float = 0.0
    rotation: float = 0.0
    opacity: float = 1.0
    volume: float = 1.0
    speed: float = 1.0
    # Text Properties
    text_content: str = ""
    font_family: str = "Segoe UI"
    font_size: int = 56
    font_color: str = "#ffffff"
    font_bold: bool = True
    font_italic: bool = False
    bg_pill: bool = False
    bg_pill_color: str = "#000000"
    alignment: str = "center"
    # Sticker Properties
    sticker_content: str = ""
    sticker_size: int = 80
    # Video Filter & Effects
    filter_type: str = "none"  # "none", "grayscale", "sepia", "invert", "warm", "cool", "high_contrast"
    # Transition
    transition_in: str = "none"
    transition_duration: float = 0.5

@dataclass
class Clip:
    media_path: str = ""
    media_type: str = "video"  # 'video', 'audio', 'image', 'text', 'sticker'
    start_time: float = 0.0  # Start time on timeline in seconds
    duration: float = 3.0  # Active duration on timeline in seconds
    source_in: float = 0.0  # In-point inside the source file
    source_out: float = 0.0  # Out-point inside the source file
    clip_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    properties: ClipProperties = field(default_factory=ClipProperties)

    def __post_init__(self):
        if not self.name:
            if self.media_type == "text":
                self.name = self.properties.text_content or "Text Element"
            elif self.media_type == "sticker":
                self.name = f"Sticker {self.properties.sticker_content}"
            elif self.media_path:
                self.name = os.path.basename(self.media_path)
            else:
                self.name = "Element"
        if self.source_out <= self.source_in:
            self.source_out = self.source_in + self.duration

    @property
    def end_time(self) -> float:
        return self.start_time + self.duration

    def contains_time(self, time_sec: float) -> bool:
        return self.start_time <= time_sec < self.end_time

    def get_source_time(self, timeline_time: float) -> float:
        """Map timeline seconds to source file seconds according to speed and in-point."""
        offset = timeline_time - self.start_time
        return self.source_in + (offset * self.properties.speed)

@dataclass
class Track:
    track_type: str  # 'video' or 'audio'
    track_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    muted: bool = False
    locked: bool = False
    clips: List[Clip] = field(default_factory=list)

    def __post_init__(self):
        if not self.name:
            prefix = "V" if self.track_type == "video" else "A"
            self.name = f"{prefix}_{self.track_id[:4]}"

    def sort_clips(self):
        self.clips.sort(key=lambda c: c.start_time)

    def add_clip(self, clip: Clip):
        self.clips.append(clip)
        self.sort_clips()

    def remove_clip(self, clip_id: str) -> Optional[Clip]:
        for i, c in enumerate(self.clips):
            if c.clip_id == clip_id:
                return self.clips.pop(i)
        return None

    def get_clip_at(self, time_sec: float) -> Optional[Clip]:
        for c in self.clips:
            if c.contains_time(time_sec):
                return c
        return None

@dataclass
class Project:
    name: str = "Untitled Project"
    width: int = 1920
    height: int = 1080
    fps: float = 30.0

class Timeline:
    def __init__(self, project: Project = None):
        self.project = project or Project()
        self.tracks: List[Track] = []
        self.playhead_time: float = 0.0
        self.selected_clip_id: Optional[str] = None
        self._init_default_tracks()

    def get_default_track(self, media_type: str) -> Track:
        if media_type in ("text", "sticker", "overlay"):
            for track in self.tracks:
                if "Overlay" in track.name or track.name == "Video 2 (Overlay)":
                    return track
            for track in self.tracks:
                if track.track_type == "video":
                    return track
        elif media_type == "video":
            for track in self.tracks:
                if "Main" in track.name or track.name == "Video 1 (Main)":
                    return track
            for track in self.tracks:
                if track.track_type == "video":
                    return track
        elif media_type == "audio":
            for track in self.tracks:
                if "Voice" in track.name or track.name == "Audio 1 (Voice)":
                    return track
            for track in self.tracks:
                if track.track_type == "audio":
                    return track
        return self.tracks[0] if self.tracks else Track(track_type=media_type)


    def _init_default_tracks(self):
        # Default 2 video tracks (overlay + main) and 2 audio tracks
        self.tracks = [
            Track(track_type="video", name="Video 2 (Overlay)"),
            Track(track_type="video", name="Video 1 (Main)"),
            Track(track_type="audio", name="Audio 1 (Voice)"),
            Track(track_type="audio", name="Audio 2 (Music)")
        ]

    @property
    def duration(self) -> float:
        max_duration = 0.0
        has_clips = False
        for track in self.tracks:
            for clip in track.clips:
                has_clips = True
                if clip.end_time > max_duration:
                    max_duration = clip.end_time
        return max_duration if has_clips else 5.0

    def find_clip_by_id(self, clip_id: str) -> Optional[tuple[Track, Clip]]:
        for track in self.tracks:
            for clip in track.clips:
                if clip.clip_id == clip_id:
                    return track, clip
        return None

    def split_clip_at(self, clip_id: str, split_time: float) -> Optional[Clip]:
        """
        Split a clip into two at split_time. Returns the newly created right-hand clip.
        """
        found = self.find_clip_by_id(clip_id)
        if not found:
            return None
        track, clip = found
        if not (clip.start_time < split_time < clip.end_time):
            return None  # Split point must be strictly inside the clip

        left_duration = split_time - clip.start_time
        right_duration = clip.duration - left_duration

        # Old clip becomes left side
        original_source_out = clip.source_out
        clip.duration = left_duration
        clip.source_out = clip.source_in + left_duration * clip.properties.speed

        # Create right side
        new_clip = Clip(
            media_path=clip.media_path,
            media_type=clip.media_type,
            start_time=split_time,
            duration=right_duration,
            source_in=clip.source_out,
            source_out=original_source_out,
            name=f"{clip.name} (Split)",
            properties=ClipProperties(
                scale_x=clip.properties.scale_x,
                scale_y=clip.properties.scale_y,
                pos_x=clip.properties.pos_x,
                pos_y=clip.properties.pos_y,
                rotation=clip.properties.rotation,
                opacity=clip.properties.opacity,
                volume=clip.properties.volume,
                speed=clip.properties.speed
            )
        )
        track.add_clip(new_clip)
        return new_clip
