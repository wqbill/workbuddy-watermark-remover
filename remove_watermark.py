"""Pure-Python Reverse Alpha Blending remover for WorkBuddy corner watermarks."""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

DEFAULT_ALPHA_PATH = Path(__file__).resolve().parent / "assets" / "workbuddy_1024_alpha.png"
SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def _imread_unicode(path: Path, flags: int) -> np.ndarray | None:
    """Read image supporting non-ASCII (e.g. Chinese) file paths on Windows."""
    data = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(data, flags) if data.size > 0 else None


def _imwrite_unicode(path: Path, image: np.ndarray) -> None:
    """Write image supporting non-ASCII file paths on Windows."""
    ext = path.suffix.lower() or ".png"
    ok, encoded = cv2.imencode(ext, image)
    if not ok:
        raise RuntimeError(f"Failed to encode image for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded.tofile(str(path))


def load_alpha(alpha_path: Path, target_shape: tuple[int, int]) -> np.ndarray:
    """Load the grayscale alpha template and resize if dimensions differ."""
    tpl = _imread_unicode(alpha_path, cv2.IMREAD_GRAYSCALE)
    if tpl is None:
        raise FileNotFoundError(f"Cannot read alpha template: {alpha_path}")

    h, w = target_shape
    if (tpl.shape[0], tpl.shape[1]) != (h, w):
        tpl = cv2.resize(tpl, (w, h), interpolation=cv2.INTER_AREA)

    return np.clip(tpl.astype(np.float32) / 255.0, 0.0, 0.99)


def remove_watermark(
    input_path: Path,
    output_path: Path,
    alpha_path: Path = DEFAULT_ALPHA_PATH,
) -> None:
    """Remove white semi-transparent corner watermark via Reverse Alpha Blending."""
    img = _imread_unicode(input_path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {input_path}")

    alpha = load_alpha(alpha_path, img.shape[:2])
    mask = alpha > 0.0
    a3 = alpha[:, :, None]

    out = img.astype(np.float32)
    out[mask] = (out[mask] - 255.0 * a3[mask]) / (1.0 - a3[mask])
    out = np.clip(out, 0, 255).round().astype(np.uint8)

    _imwrite_unicode(output_path, out)


def process_path(
    input_path: Path,
    output_path: Path | None,
    alpha_path: Path = DEFAULT_ALPHA_PATH,
) -> list[Path]:
    """Process a single image file or all supported images in a directory."""
    if input_path.is_dir():
        out_dir = output_path or input_path / "cleaned"
        results: list[Path] = []
        for file in sorted(input_path.iterdir()):
            if file.is_file() and file.suffix.lower() in SUPPORTED_EXTS:
                dst = out_dir / f"{file.stem}_clean.png"
                remove_watermark(file, dst, alpha_path)
                results.append(dst)
        return results

    dst = output_path or input_path.with_name(f"{input_path.stem}_clean.png")
    remove_watermark(input_path, dst, alpha_path)
    return [dst]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove WorkBuddy corner watermark via Reverse Alpha Blending."
    )
    parser.add_argument("input", type=Path, help="Input watermarked image or directory")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output image path or directory (default: <stem>_clean.png or <input>/cleaned)",
    )
    parser.add_argument(
        "--alpha",
        type=Path,
        default=DEFAULT_ALPHA_PATH,
        help="Alpha template path (default: assets/workbuddy_1024_alpha.png)",
    )
    args = parser.parse_args()

    outputs = process_path(args.input, args.output, args.alpha)
    for out in outputs:
        print(f"Saved cleaned image to {out}")


if __name__ == "__main__":
    main()
