import math
import tempfile

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


class ImageEnhancer:
    @staticmethod
    def enhance(input_path: str, deskew: bool = True, sharpen: bool = True,
                contrast: bool = True, threshold: bool = False) -> str:
        """Enhance a document photo. Returns path to temp file with result."""
        img = Image.open(input_path).convert("RGB")

        if deskew:
            img = ImageEnhancer._deskew(img)
        if sharpen:
            img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        if contrast:
            img = ImageEnhance.Contrast(img).enhance(1.5)
        if threshold:
            img = ImageEnhancer._adaptive_threshold(img)

        out = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img.save(out.name)
        return out.name

    @staticmethod
    def _deskew(img: Image.Image) -> Image.Image:
        """Detect skew angle via Hough lines and rotate to straighten."""
        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(cv_img, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, math.pi / 180, threshold=100,
                                minLineLength=cv_img.shape[1] // 4, maxLineGap=10)
        if lines is None:
            return img

        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
            # Only consider near-horizontal lines (within 45 degrees)
            if abs(angle) < 45:
                angles.append(angle)

        if not angles:
            return img

        median_angle = float(np.median(angles))
        # Only correct if skew is meaningful but not too large
        if abs(median_angle) < 0.5 or abs(median_angle) > 15:
            return img

        return img.rotate(median_angle, expand=True, fillcolor=(255, 255, 255),
                          resample=Image.BICUBIC)

    @staticmethod
    def _adaptive_threshold(img: Image.Image) -> Image.Image:
        """Apply adaptive threshold for a clean black-and-white document look."""
        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
        binary = cv2.adaptiveThreshold(cv_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 21, 10)
        return Image.fromarray(binary).convert("RGB")
