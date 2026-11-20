"""Unit tests for WorkBuddy Reverse Alpha Blending watermark remover."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from extract_alpha import extract_alpha  # noqa: E402
from remove_watermark import DEFAULT_ALPHA_PATH, remove_watermark  # noqa: E402


class TestWatermarkRemover(unittest.TestCase):
    def test_non_watermark_region_untouched(self) -> None:
        inp = PROJECT_ROOT / "examples" / "input.png"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.png"
            remove_watermark(inp, out, DEFAULT_ALPHA_PATH)
            self.assertTrue(out.exists())

            src_img = cv2.imread(str(inp))
            out_img = cv2.imread(str(out))
            self.assertEqual(src_img.shape, out_img.shape)
            # Top-left 80% of the image has alpha == 0 and must be bit-identical
            self.assertTrue(np.array_equal(src_img[:800, :800], out_img[:800, :800]))

    def test_black_reference_restores_to_black(self) -> None:
        black_ref = PROJECT_ROOT / "examples" / "black_ref.png"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "black_clean.png"
            remove_watermark(black_ref, out, DEFAULT_ALPHA_PATH)
            cleaned = cv2.imread(str(out))
            self.assertLessEqual(int(cleaned.max()), 3)

    def test_extract_alpha_from_black_ref(self) -> None:
        black_ref = PROJECT_ROOT / "examples" / "black_ref.png"
        with tempfile.TemporaryDirectory() as tmp:
            alpha_out = Path(tmp) / "alpha.png"
            extract_alpha(black_ref, alpha_out)
            alpha = cv2.imread(str(alpha_out), cv2.IMREAD_GRAYSCALE)
            self.assertEqual(alpha.shape, (1024, 1024))
            self.assertGreater(int(alpha.max()), 100)
            self.assertEqual(int(alpha[:800, :800].max()), 0)


if __name__ == "__main__":
    unittest.main()
