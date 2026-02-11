"""
Utility functions for handling media content (images, etc.) in TinyTroupe.

Provides helpers for converting image references (file paths, URLs, data URIs)
into the multimodal content format required by the OpenAI vision API.
"""

import base64
import hashlib
import logging
import mimetypes
import os
from typing import Union

logger = logging.getLogger("tinytroupe")


def _mime_type_for_image(path: str) -> str:
    """Infer MIME type from a file path or URL, defaulting to image/png."""
    mime, _ = mimetypes.guess_type(path)
    if mime and mime.startswith("image/"):
        return mime
    # fallback based on common extensions
    ext = os.path.splitext(path)[-1].lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }.get(ext, "image/png")


def normalize_image_to_openai_url(image_ref: str) -> str:
    """
    Convert an image reference to a URL suitable for the OpenAI vision API.

    - If ``image_ref`` is already a URL (http/https) or a data URI, return as-is.
    - If it is a local file path, read the file, base64-encode it, and return a
      ``data:<mime>;base64,...`` URI.

    Args:
        image_ref: A file path, URL, or data URI pointing to an image.

    Returns:
        A URL string ready for the OpenAI ``image_url`` content part.
    """
    if image_ref.startswith(("http://", "https://", "data:")):
        return image_ref

    # Local file path — read and encode
    abs_path = os.path.abspath(image_ref)
    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f"Image file not found: {abs_path}")

    mime = _mime_type_for_image(abs_path)
    with open(abs_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def build_multimodal_content_array(
    text: str,
    image_refs: list[str],
    detail: str = "auto",
) -> list[dict]:
    """
    Build an OpenAI-compatible multimodal content array from text and images.

    The resulting list can be used directly as the ``content`` field of a message
    in the chat completions API when vision is required.

    Args:
        text: The text part of the message.
        image_refs: A list of image references (file paths, URLs, or data URIs).
        detail: The detail level for the images (``"auto"``, ``"low"``, or ``"high"``).

    Returns:
        A list of content parts, e.g.::

            [
                {"type": "text", "text": "..."},
                {"type": "image_url", "image_url": {"url": "...", "detail": "auto"}},
                ...
            ]
    """
    parts: list[dict] = []

    if text:
        parts.append({"type": "text", "text": text})

    for ref in image_refs:
        url = normalize_image_to_openai_url(ref)
        parts.append({
            "type": "image_url",
            "image_url": {"url": url, "detail": detail},
        })

    return parts


def hash_image(image_ref: str) -> str:
    """
    Compute a stable hash for an image reference, suitable for caching.

    - For local files, hashes the file content (SHA-256).
    - For URLs, hashes the URL string itself.
    - For data URIs, hashes the full URI string.

    Args:
        image_ref: A file path, URL, or data URI.

    Returns:
        A hex-encoded SHA-256 hash string.
    """
    if image_ref.startswith(("http://", "https://", "data:")):
        return hashlib.sha256(image_ref.encode("utf-8")).hexdigest()

    abs_path = os.path.abspath(image_ref)
    sha = hashlib.sha256()
    with open(abs_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


def normalize_image_refs(images: Union[None, str, list]) -> list[str]:
    """
    Normalize the ``images`` parameter into a flat list of image reference strings.

    Accepts None, a single string, or a list of strings.

    Args:
        images: The raw images parameter as passed by the user.

    Returns:
        A (possibly empty) list of image reference strings.
    """
    if images is None:
        return []
    if isinstance(images, str):
        return [images]
    return list(images)
