"""Deliver the finished news poster as this entry's output image.

The poster itself is rendered by the build pipeline in this repository
(main renderer history in git: illustrations.py + layout.py paint the
broadsheet from stories.json) and committed beside this program as
``poster.png``.  Running the program validates that the poster is a
well-formed PNG inside every bounty limit, copies it byte for byte to
``entry.png`` in the output folder, and reads the copy back to prove
the delivery is exact.  Standard library only, and nothing is written
beside the program, so the entry runs unchanged on a read-only mount
under ``python3 -P -s``.
"""

import os
import struct
import sys
from pathlib import Path

POSTER_NAME = "poster.png"
ENTRY_NAME = "entry.png"
MAX_FILE_BYTES = 1_572_864  # 1.5 MiB hard limit for the delivered image
MAX_SIDE_PIXELS = 4096
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
FALLBACK_OUTPUT_DIR = "/output"


def validate_poster(data: bytes) -> tuple[int, int]:
    """Check the poster against every bounty rule; return (width, height)."""
    if len(data) > MAX_FILE_BYTES:
        raise ValueError(f"poster is {len(data)} bytes; the limit is {MAX_FILE_BYTES}")
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("poster does not start with the PNG signature")
    # IHDR is the first chunk: 8-byte signature, 4-byte length, "IHDR",
    # then width and height as big-endian uint32.
    if len(data) < 33 or data[12:16] != b"IHDR":
        raise ValueError("poster has no IHDR chunk")
    width, height = struct.unpack(">II", data[16:24])
    if width == 0 or height == 0:
        raise ValueError("poster reports a zero width or height")
    if width > MAX_SIDE_PIXELS or height > MAX_SIDE_PIXELS:
        raise ValueError(
            f"poster is {width}x{height}; the limit is {MAX_SIDE_PIXELS}x{MAX_SIDE_PIXELS}"
        )
    return width, height


def output_folder() -> Path:
    folder = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or FALLBACK_OUTPUT_DIR)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def deliver() -> tuple[Path, int, int]:
    """Validate the poster beside this program and copy it to the output."""
    poster_path = Path(__file__).resolve().parent / POSTER_NAME
    data = poster_path.read_bytes()
    width, height = validate_poster(data)
    target = output_folder() / ENTRY_NAME
    target.write_bytes(data)
    if target.read_bytes() != data:
        raise ValueError("the written entry.png differs from poster.png")
    return target, width, height


def main() -> int:
    target, width, height = deliver()
    print(f"wrote {target} ({width}x{height})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
