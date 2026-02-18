import math
import tempfile

import cv2
import numpy as np


class ImageEnhancer:
    @staticmethod
    def enhance(input_path: str, deskew: bool = True, sharpen: bool = True,
                contrast: bool = True, threshold: bool = True) -> str:
        """Enhance a document photo for scanner-like output. Returns path to temp PNG."""
        gray = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
        if gray is None:
            # Fallback: load via PIL (e.g. for unusual formats) and convert
            from PIL import Image
            gray = np.array(Image.open(input_path).convert("L"))

        if deskew:
            gray = ImageEnhancer._deskew(gray)
        if sharpen:
            gray = ImageEnhancer._sharpen(gray)
        if contrast:
            gray = ImageEnhancer._clahe(gray)
        if threshold:
            gray = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                21, 10,
            )

        out = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        cv2.imwrite(out.name, gray)
        return out.name

    @staticmethod
    def _deskew(gray: np.ndarray) -> np.ndarray:
        """Detect skew angle via Hough lines and rotate to straighten."""
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(
            edges, 1, math.pi / 180, threshold=100,
            minLineLength=gray.shape[1] // 4, maxLineGap=10,
        )
        if lines is None:
            return gray

        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
            if abs(angle) < 45:
                angles.append(angle)

        if not angles:
            return gray

        median_angle = float(np.median(angles))
        if abs(median_angle) < 0.5 or abs(median_angle) > 15:
            return gray

        h, w = gray.shape
        M = cv2.getRotationMatrix2D((w / 2, h / 2), median_angle, 1.0)
        return cv2.warpAffine(
            gray, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

    @staticmethod
    def _sharpen(gray: np.ndarray) -> np.ndarray:
        """Unsharp mask via Gaussian blur subtraction."""
        blurred = cv2.GaussianBlur(gray, (0, 0), 2)
        return cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)

    @staticmethod
    def _clahe(gray: np.ndarray) -> np.ndarray:
        """CLAHE: adaptive histogram equalisation for uneven lighting."""
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(gray)
