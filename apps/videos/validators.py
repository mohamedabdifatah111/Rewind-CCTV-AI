import os
from django.conf import settings
from rest_framework import serializers

MIME_BY_EXT = {"mp4": {"video/mp4"}, "mov": {"video/quicktime", "video/mp4"}, "avi": {"video/x-msvideo", "video/avi", "video/msvideo"}}
CANONICAL = {"mp4": "video/mp4", "mov": "video/quicktime", "avi": "video/x-msvideo"}
VENDOR_BOXES = {b"moov", b"mdat", b"wide", b"free", b"skip"}

def validate_video_upload(f):
    """Checks extension, declared MIME, size, and the file's own magic bytes. Returns (ext, canonical_mime)."""
    if not f.size:
        raise serializers.ValidationError("The uploaded file is empty.")
    limit = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if f.size > limit:
        raise serializers.ValidationError(f"File is too large. The limit is {settings.MAX_UPLOAD_SIZE_MB} MB.")
    ext = os.path.splitext(f.name or "")[1].lower().lstrip(".")
    if ext not in MIME_BY_EXT:
        raise serializers.ValidationError(f"Unsupported file type. Allowed: {', '.join(settings.SUPPORTED_FORMATS)}.")
    declared = (getattr(f, "content_type", "") or "").split(";")[0].strip().lower()
    if declared and declared != "application/octet-stream" and declared not in MIME_BY_EXT[ext]:
        raise serializers.ValidationError("The declared content type does not match the file extension.")
    head = f.read(12); f.seek(0)  # never trust name or MIME alone: check the container signature
    ok = (head[4:8] == b"ftyp" or head[4:8] in VENDOR_BOXES) if ext in ("mp4", "mov") else (head[:4] == b"RIFF" and head[8:12] == b"AVI ")
    if not ok:
        raise serializers.ValidationError("The file contents do not look like a valid video of that type.")
    return ext, CANONICAL[ext]
