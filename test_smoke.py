import sys
import os
from PyQt6.QtWidgets import QApplication

def run_test():
    print("Initializing test...")
    app = QApplication(sys.argv + ['-platform', 'offscreen'])

    from core.models import Timeline, Project, Clip
    from engine.media_reader import MediaReader
    from engine.compositor import Compositor
    from export.exporter import ExportWorker

    media_path = os.path.abspath('test_sample.mp4')
    if not os.path.exists(media_path):
        print("Error: test_sample.mp4 not found!")
        return

    reader = MediaReader(media_path)
    print(f"Video info: {reader.info.width}x{reader.info.height}, duration={reader.info.duration:.2f}s, fps={reader.info.fps}")

    timeline = Timeline(Project(width=1280, height=720, fps=30))
    clip = Clip(media_path=media_path, media_type='video', start_time=0.0, duration=3.0)
    timeline.tracks[1].add_clip(clip)

    print(f"Timeline duration: {timeline.duration:.2f}s")
    compositor = Compositor(timeline)
    frame = compositor.render_frame(1.5)
    print(f"Rendered frame size: {frame.width()}x{frame.height()}, isNull={frame.isNull()}")

    # Test split
    new_clip = timeline.split_clip_at(clip.clip_id, 1.0)
    if new_clip:
        print(f"Split success! Left clip: [0.0s -> {clip.duration:.2f}s], Right clip: [{new_clip.start_time:.2f}s -> {new_clip.end_time:.2f}s]")
    else:
        print("Split failed!")

    # Test export
    output_path = os.path.abspath('test_export.mp4')
    print("Testing export to:", output_path)
    worker = ExportWorker(timeline, output_path)
    worker.run()

    if os.path.exists(output_path):
        print(f"Export SUCCESS! File size: {os.path.getsize(output_path)} bytes")
    else:
        print("Export failed: Output file not created.")

if __name__ == "__main__":
    run_test()
