"""Extract an exact corner alpha template from a pure-black reference image."""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


def extract_alpha(
    black_ref_path: Path,
    output_path: Path,
    roi_x_start: float = 0.85,
    roi_y_start: float = 0.92,
    noise_threshold: int = 3,
) -> None:
    """Extract grayscale alpha mask (0-255) from a pure-black watermarked image."""
    img = cv2.imread(str(black_ref_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Cannot read reference image: {black_ref_path}")

    h, w = img.shape
    mask = np.zeros((h, w), dtype=np.uint8)

    y0 = int(h * roi_y_start)
    x0 = int(w * roi_x_start)
    roi = img[y0:h, x0:w].copy()
    roi[roi <= noise_threshold] = 0
    mask[y0:h, x0:w] = roi

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), mask)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract WorkBuddy watermark alpha template from a pure-black image."
    )
    parser.add_argument("input", type=Path, help="Pure-black reference image path")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("assets/workbuddy_1024_alpha.png"),
        help="Output alpha template path",
    )
    args = parser.parse_args()
    extract_alpha(args.input, args.output)
    print(f"Saved alpha template to {args.output}")


if __name__ == "__main__":
    main()
