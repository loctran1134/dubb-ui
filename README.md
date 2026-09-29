# DubbCut - Native PyQt6 Video Editor (OpenCut Architecture)

Ứng dụng biên tập video Desktop Native 100% bằng **PyQt6**, **PyAV (FFmpeg C-bindings)** và **FFmpeg CLI**.
Dự án được thiết kế theo đúng kiến trúc và giao diện chuyên nghiệp của **OpenCut / CapCut**, **tuyệt đối không sử dụng server ngầm, webview hay các giải pháp bọc trình duyệt giả lập**.

---

## 1. Kiến trúc hệ thống (Architecture)

```
dubbcut/
├── core/
│   ├── timecode.py         # Quy đổi SMPTE Timecode, frame index và giây
│   └── models.py           # Data Model thuần: Project, Timeline, Track, Clip, ClipProperties
├── engine/
│   ├── media_reader.py     # Lõi giải mã video frame-accurate bằng PyAV với bộ đệm phát luồng tiến
│   ├── compositor.py       # Trộn khung hình đa track (layers blending) kèm affine transforms
│   └── player.py           # Bộ điều khiển nhịp phát thời gian thực (Playback Controller)
├── gui/
│   ├── styles.py           # Giao diện Dark Theme chuyên nghiệp phong cách CapCut / OpenCut
│   ├── preview_widget.py   # Màn hình xem trước video + Canvas giữ tỉ lệ + Bảng timecode
│   ├── inspector_widget.py # Bảng chỉnh thuộc tính clip (Scale, Position X/Y, Rotation, Opacity, Volume)
│   ├── media_library_widget.py # Thư viện Asset (Import video/audio/ảnh, thumbnail, thời lượng)
│   ├── export_dialog.py    # Cửa sổ xuất video với thanh tiến trình thực tế
│   ├── main_window.py      # Cửa sổ chính điều phối 4 panels qua QSplitter
│   └── timeline/
│       ├── ruler.py        # Thước đo thời gian tương tác (Time Ruler) kèm con trỏ Playhead
│       ├── clip_item.py    # Widget Clip trên timeline (kéo di chuyển, kéo 2 mép để trim)
│       └── timeline_view.py # Khung timeline đa track (V2 Overlay, V1 Main, A1, A2) kèm thanh công cụ
├── export/
│   └── exporter.py         # Worker thread xuất video stream frame thô trực tiếp vào native FFmpeg
├── main.py                 # File khởi chạy ứng dụng (Hỗ trợ High-DPI)
└── run.bat                 # File click chạy nhanh trên Windows
```

---

## 2. Các phím tắt tiện ích (Hotkeys)

*   `Space`: Bật / Tạm dừng phát video (Play / Pause).
*   `S` hoặc `Ctrl + B`: Cắt đôi clip đang chọn tại vị trí con trỏ Playhead (Split).
*   `Delete` hoặc `Backspace`: Xóa clip đang chọn trên timeline.
*   `Phím mũi tên Trái (←)`: Lùi lại 1 frame.
*   `Phím mũi tên Phải (→)`: Tiến tới 1 frame.

---

## 3. Cách khởi chạy ứng dụng

### Cách 1: Click chuột
*   Nhấp đúp chuột vào file `run.bat` trong thư mục `d:\dubbcut`.

### Cách 2: Chạy lệnh từ Terminal
```bash
cd d:\dubbcut
.\.venv\Scripts\python.exe main.py
```
