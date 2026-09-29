from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QCursor, QLinearGradient, QPixmap, QPainterPath
from PyQt6.QtCore import Qt, QRectF, QPointF, QSize
from core.models import Clip, Track
from engine.media_reader import MediaReader

class ClipItem(QGraphicsRectItem):
    """
    OpenCut Timeline Element with Tiled Thumbnail Filmstrip, Audio Waveforms,
    MediaElementHeader gradient, and signature #009dff Selection Ring.
    """
    HANDLE_WIDTH = 6.0

    def __init__(self, clip: Clip, track: Track, track_index: int, px_per_sec: float, track_height: float = 48.0):
        super().__init__()
        self.clip = clip
        self.track = track
        self.track_index = track_index
        self.px_per_sec = px_per_sec
        self.track_height = track_height
        self._thumbnail: QPixmap = None
        self._load_thumbnail()

        self.on_clip_clicked = None
        self.on_clip_modified = None

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)

        self._drag_mode = None
        self._drag_start_pos = QPointF()
        self._original_start_time = clip.start_time
        self._original_duration = clip.duration
        self._original_source_in = clip.source_in
        self._original_source_out = clip.source_out

        self.update_geometry()

    def _load_thumbnail(self):
        if self.clip.media_type == "video":
            try:
                reader = MediaReader(self.clip.media_path)
                tile_h = int(self.track_height)
                tile_w = int(tile_h * (16.0 / 9.0))
                # Seek to frame near clip's in-point
                thumb_time = max(0.0, self.clip.source_in + 0.2)
                frame = reader.get_frame_at_time(thumb_time)
                if frame is not None:
                    pix = QPixmap.fromImage(frame)
                    self._thumbnail = pix.scaled(
                        tile_w, tile_h,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                else:
                    self._thumbnail = reader.generate_thumbnail(tile_w, tile_h)
                reader.close()
            except Exception:
                self._thumbnail = None

    def update_geometry(self):
        x = self.clip.start_time * self.px_per_sec
        y = self.track_index * self.track_height + 2
        w = max(10.0, self.clip.duration * self.px_per_sec)
        h = self.track_height - 4

        self.setRect(0, 0, w, h)
        self.setPos(x, y)

    def set_zoom(self, px_per_sec: float):
        self.px_per_sec = px_per_sec
        self.update_geometry()

    def hoverMoveEvent(self, event):
        pos_x = event.pos().x()
        w = self.rect().width()

        if pos_x <= self.HANDLE_WIDTH or pos_x >= w - self.HANDLE_WIDTH:
            self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Guarantee single item selection
            if self.scene():
                for it in self.scene().selectedItems():
                    if it is not self:
                        it.setSelected(False)
            self.setSelected(True)

            pos_x = event.pos().x()
            w = self.rect().width()

            self._drag_start_pos = event.scenePos()
            self._original_start_time = self.clip.start_time
            self._original_duration = self.clip.duration
            self._original_source_in = self.clip.source_in
            self._original_source_out = self.clip.source_out

            if pos_x <= self.HANDLE_WIDTH:
                self._drag_mode = 'trim_left'
            elif pos_x >= w - self.HANDLE_WIDTH:
                self._drag_mode = 'trim_right'
            else:
                self._drag_mode = 'move'

            # Notify playhead scrub on click
            click_time = self.clip.start_time + max(0.0, min(self.clip.duration, pos_x / self.px_per_sec))
            if callable(self.on_clip_clicked):
                self.on_clip_clicked(self.clip, click_time)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_mode is not None:
            delta_x = event.scenePos().x() - self._drag_start_pos.x()
            delta_sec = delta_x / self.px_per_sec

            if self._drag_mode == 'move':
                new_start = max(0.0, self._original_start_time + delta_sec)
                self.clip.start_time = new_start
                self.update_geometry()
                if callable(self.on_clip_clicked):
                    self.on_clip_clicked(self.clip, new_start)

            elif self._drag_mode == 'trim_right':
                min_duration = 0.15
                new_duration = max(min_duration, self._original_duration + delta_sec)
                self.clip.duration = new_duration
                self.clip.source_out = self.clip.source_in + new_duration * self.clip.properties.speed
                self.update_geometry()
                if callable(self.on_clip_clicked):
                    self.on_clip_clicked(self.clip, self.clip.end_time)

            elif self._drag_mode == 'trim_left':
                min_duration = 0.15
                if delta_sec < self._original_duration - min_duration:
                    new_start = max(0.0, self._original_start_time + delta_sec)
                    new_duration = self._original_duration - delta_sec
                    self.clip.start_time = new_start
                    self.clip.duration = new_duration
                    self.clip.source_in = self._original_source_in + delta_sec * self.clip.properties.speed
                    self.update_geometry()
                    if callable(self.on_clip_clicked):
                        self.on_clip_clicked(self.clip, new_start)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        was_dragging = self._drag_mode is not None
        self._drag_mode = None
        self.track.sort_clips()
        super().mouseReleaseEvent(event)

        if was_dragging and callable(self.on_clip_modified):
            self.on_clip_modified(self.clip)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = self.rect()
        is_sel = self.isSelected()

        # 1. Base Element Colors according to OpenCut theme.ts
        if self.clip.media_type == "video":
            bg_color = QColor(24, 24, 27)  # muted dark
        elif self.clip.media_type == "audio":
            bg_color = QColor(143, 93, 186)  # OpenCut #8F5DBA
        elif self.clip.media_type == "text":
            bg_color = QColor(43, 138, 114)  # OpenCut #5DBAA0
        elif self.clip.media_type == "sticker":
            bg_color = QColor(180, 83, 9)  # Amber
        else:
            bg_color = QColor(39, 39, 42)

        painter.save()

        # Clip entire rendering inside 4px rounded path so filmstrip does not bleed outside corners
        path = QPainterPath()
        path.addRoundedRect(rect, 4.0, 4.0)
        painter.setClipPath(path)

        # Draw base container background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRect(rect)

        # 2. Tiled Media Filmstrip (Exact OpenCut TiledMediaContent)
        if self.clip.media_type == "video" and self._thumbnail and not self._thumbnail.isNull():
            tile_h = int(rect.height())
            tile_w = int(tile_h * (16.0 / 9.0))
            cur_x = 0
            while cur_x < rect.width():
                draw_w = min(tile_w, int(rect.width() - cur_x))
                painter.drawPixmap(int(cur_x), 0, self._thumbnail, 0, 0, draw_w, tile_h)
                # Subtle filmstrip seam
                painter.setPen(QColor(0, 0, 0, 75))
                painter.drawLine(int(cur_x + draw_w), 0, int(cur_x + draw_w), tile_h)
                cur_x += tile_w

        # 3. Audio Waveform Lines (for Audio tracks)
        if self.clip.media_type == "audio":
            painter.setPen(QPen(QColor(255, 255, 255, 180), 1))
            mid_y = rect.height() / 2.0
            x = 6.0
            while x < rect.width() - 6:
                amp = 3.0 + (abs(int(x * 13) % 28) - 14)
                painter.drawLine(int(x), int(mid_y - amp), int(x), int(mid_y + amp))
                x += 3.5

        # 4. Text or Sticker Content Display
        if self.clip.media_type == "text":
            painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            painter.setPen(QColor(255, 255, 255, 90))
            painter.drawText(QRectF(10, 16, rect.width() - 20, rect.height() - 16), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "T")

        if self.clip.media_type == "sticker":
            painter.setFont(QFont("Segoe UI Emoji", 14))
            painter.drawText(QRectF(10, 16, rect.width() - 20, rect.height() - 16), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.clip.properties.sticker_content or "⭐")

        # 4. Top Gradient Overlay & Header (OpenCut MediaElementHeader)
        header_h = 18.0
        grad = QLinearGradient(0, 0, 0, header_h)
        grad.setColorAt(0.0, QColor(0, 0, 0, 160))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawRect(QRectF(0, 0, rect.width(), header_h))

        # Title Text in OpenCut micro typography (text-[0.6rem] text-white/80)
        painter.setFont(QFont("Segoe UI", 7, QFont.Weight.DemiBold))
        painter.setPen(QColor(255, 255, 255, 220))
        title_rect = QRectF(6, 1, rect.width() - 12, 14)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.clip.name)

        painter.restore()

        # 5. Selection Ring (Exact OpenCut var(--primary) #009dff border)
        if is_sel:
            border_rect = rect.adjusted(1, 1, -1, -1)
            painter.setPen(QPen(QColor(0, 157, 255), 2.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(border_rect, 4, 4)

            # Left and Right Resize Grips
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(1, rect.height() / 2 - 8, 3, 16), 1.5, 1.5)
            painter.drawRoundedRect(QRectF(rect.width() - 4, rect.height() / 2 - 8, 3, 16), 1.5, 1.5)
        else:
            border_rect = rect.adjusted(0.5, 0.5, -0.5, -0.5)
            painter.setPen(QPen(QColor(255, 255, 255, 25), 1.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(border_rect, 4, 4)
