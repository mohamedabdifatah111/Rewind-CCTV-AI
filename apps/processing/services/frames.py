"""Frame sampling with OpenCV. Streams the file: only one decoded frame is held at a time."""
import math, shutil, subprocess
from dataclasses import dataclass
import cv2

class VideoReadError(Exception):
    pass

@dataclass
class VideoInfo:
    duration: float | None
    fps: float | None
    frame_count: int | None

@dataclass
class SampledFrame:
    frame_number: int
    timestamp: float  # seconds from start of video
    jpeg: bytes

def _valid_fps(fps):
    return bool(fps) and 0 < fps < 1000

def _ffprobe_duration(path):
    if not shutil.which("ffprobe"):
        return None
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                             capture_output=True, text=True, timeout=30).stdout.strip()
        d = float(out)
        return d if d > 0 else None
    except (ValueError, subprocess.SubprocessError, OSError):
        return None

def probe_video(path) -> VideoInfo:
    """Read metadata. Raises VideoReadError if the file cannot be opened or decoded."""
    cap = cv2.VideoCapture(path)
    try:
        if not cap.isOpened():
            raise VideoReadError("The file could not be opened as a video (corrupt or unsupported codec).")
        fps = cap.get(cv2.CAP_PROP_FPS)
        count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        ok, _ = cap.read()
        if not ok:
            raise VideoReadError("The video has no decodable frames (corrupt or unsupported codec).")
    finally:
        cap.release()
    fps = fps if _valid_fps(fps) else None
    duration = count / fps if fps and count > 0 else _ffprobe_duration(path)  # metadata may be missing/invalid
    return VideoInfo(duration=duration, fps=fps, frame_count=count if count > 0 else None)

def estimate_total(duration, interval):
    return math.ceil(duration / interval) if duration else 0

def iter_sampled_frames(path, interval, max_side=1024):
    """Yield a JPEG every `interval` seconds starting at t=0.

    Frames are visited sequentially (grab) so the timestamp of each sampled frame is exact:
    frame_number / fps, or the container's own position when fps metadata is invalid.
    Sparse sampling can miss anything that happens between samples.
    """
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise VideoReadError("The file could not be opened as a video.")
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        use_fps = _valid_fps(fps)
        next_t, idx, yielded = 0.0, -1, 0
        while cap.grab():
            idx += 1
            t = idx / fps if use_fps else max(cap.get(cv2.CAP_PROP_POS_MSEC), 0) / 1000.0
            if t + 1e-6 < next_t:
                continue
            ok, frame = cap.retrieve()
            if not ok:
                continue  # undecodable frame: skip, try the next sample point
            h, w = frame.shape[:2]
            scale = max_side / max(h, w)
            if scale < 1:
                frame = cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ok:
                continue
            yield SampledFrame(idx, round(t, 3), buf.tobytes())
            yielded += 1
            while next_t <= t + 1e-6:
                next_t += interval
        if yielded == 0:
            raise VideoReadError("No frames could be decoded from this video.")
    finally:
        cap.release()
