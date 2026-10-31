import os, tempfile
import cv2, numpy as np

def make_video(path, seconds=5, fps=10, size=(160, 120), fourcc="mp4v"):
    """Write a synthetic video whose brightness changes every frame."""
    w = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*fourcc), fps, size)
    for i in range(int(seconds * fps)):
        w.write(np.full((size[1], size[0], 3), (i * 5) % 255, dtype=np.uint8))
    w.release()
    return path

def video_bytes(**kw):
    fd, p = tempfile.mkstemp(suffix=".mp4"); os.close(fd)
    try:
        make_video(p, **kw)
        with open(p, "rb") as f: return f.read()
    finally:
        os.remove(p)
