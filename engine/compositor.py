from PyQt6.QtGui import QImage, QPainter, QColor, QFont, QPen, QBrush
from PyQt6.QtCore import Qt, QRectF, QPointF
from typing import Dict, List, Optional
from core.models import Timeline, Clip, Track, ClipProperties
from engine.media_reader import MediaReader

class Compositor:
    """
    Multi-track video frame compositor.
    Blends video tracks in layer order with affine transforms, alpha blending,
    real-time video filters (Grayscale, Sepia, Invert, Warm, Cool),
    and rich Text & Sticker elements.
    """
    def __init__(self, timeline: Timeline):
        self.timeline = timeline
        self.readers: Dict[str, MediaReader] = {}

    def get_reader(self, path: str) -> Optional[MediaReader]:
        if not path:
            return None
        if path not in self.readers:
            self.readers[path] = MediaReader(path)
        return self.readers[path]

    def render_frame(self, time_sec: float) -> QImage:
        """
        Synthesize canvas frame at time_sec across all active video/overlay tracks.
        """
        proj = self.timeline.project
        canvas = QImage(proj.width, proj.height, QImage.Format.Format_ARGB32_Premultiplied)
        canvas.fill(QColor(18, 18, 20))  # Slate dark canvas background

        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        # Video tracks are rendered from bottom track (base) to top track (overlay)
        video_tracks = [t for t in self.timeline.tracks if t.track_type == "video" and not t.muted]
        video_tracks_ordered = sorted(video_tracks, key=lambda t: t.name, reverse=False)

        for track in video_tracks_ordered:
            clip = track.get_clip_at(time_sec)
            if clip is None:
                continue

            props = clip.properties
            painter.save()

            # Center-relative affine transformations
            cx = proj.width / 2.0 + props.pos_x
            cy = proj.height / 2.0 + props.pos_y

            painter.translate(cx, cy)
            if props.rotation != 0:
                painter.rotate(props.rotation)
            if props.scale_x != 1.0 or props.scale_y != 1.0:
                painter.scale(props.scale_x, props.scale_y)
            if props.opacity < 1.0:
                painter.setOpacity(max(0.0, min(1.0, props.opacity)))

            # Render by element type
            if clip.media_type in ("video", "image"):
                if clip.media_path:
                    source_time = clip.get_source_time(time_sec)
                    reader = self.get_reader(clip.media_path)
                    if reader:
                        frame_img = reader.get_frame_at_time(source_time)
                        if frame_img is not None and not frame_img.isNull():
                            filtered_img = self._apply_filter(frame_img, props.filter_type)
                            fw = filtered_img.width()
                            fh = filtered_img.height()
                            target_rect = QRectF(-fw / 2.0, -fh / 2.0, fw, fh)
                            painter.drawImage(target_rect, filtered_img)

            elif clip.media_type == "text":
                self._draw_text_element(painter, clip, props)

            elif clip.media_type == "sticker":
                self._draw_sticker_element(painter, clip, props)

            painter.restore()

        painter.end()
        return canvas

    def _apply_filter(self, img: QImage, filter_type: str) -> QImage:
        if filter_type == "none" or not filter_type:
            return img

        if filter_type == "grayscale":
            return img.convertToFormat(QImage.Format.Format_Grayscale8).convertToFormat(QImage.Format.Format_RGB888)

        elif filter_type == "invert":
            res = img.copy()
            res.invertPixels()
            return res

        elif filter_type in ("sepia", "warm", "cool", "high_contrast"):
            res = img.copy()
            p = QPainter(res)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
            if filter_type == "sepia":
                p.fillRect(res.rect(), QColor(255, 230, 190))
            elif filter_type == "warm":
                p.fillRect(res.rect(), QColor(255, 215, 175))
            elif filter_type == "cool":
                p.fillRect(res.rect(), QColor(180, 215, 255))
            elif filter_type == "high_contrast":
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Overlay)
                p.fillRect(res.rect(), QColor(128, 128, 128, 180))
            p.end()
            return res

        return img

    def _draw_text_element(self, painter: QPainter, clip: Clip, props: ClipProperties):
        text = props.text_content or clip.name or "Title"
        font = QFont(props.font_family, props.font_size)
        font.setBold(props.font_bold)
        font.setItalic(props.font_italic)
        painter.setFont(font)

        fm = painter.fontMetrics()
        bounds = fm.boundingRect(text)
        w = max(100.0, bounds.width() + 40.0)
        h = max(40.0, bounds.height() + 20.0)
        rect = QRectF(-w / 2.0, -h / 2.0, w, h)

        if props.bg_pill:
            painter.setPen(Qt.PenStyle.NoPen)
            pill_color = QColor(props.bg_pill_color) if props.bg_pill_color else QColor(0, 0, 0, 180)
            painter.setBrush(QBrush(pill_color))
            painter.drawRoundedRect(rect, 8, 8)

        painter.setPen(QColor(props.font_color or "#ffffff"))
        align_flag = Qt.AlignmentFlag.AlignCenter
        if props.alignment == "left":
            align_flag = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        elif props.alignment == "right":
            align_flag = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

        painter.drawText(rect, align_flag, text)

    def _draw_sticker_element(self, painter: QPainter, clip: Clip, props: ClipProperties):
        sticker = props.sticker_content or "🔥"
        size = props.sticker_size or 80
        font = QFont("Segoe UI Emoji", size)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        rect = QRectF(-size, -size, size * 2, size * 2)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, sticker)

    def cleanup(self):
        for reader in self.readers.values():
            reader.close()
        self.readers.clear()
