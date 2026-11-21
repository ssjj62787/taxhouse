"""스마트폰 촬영 사진 전처리: 기울기 보정, 흑백화, 대비 강화.

OCR 정확도를 높이기 위한 최소한의 처리만 수행합니다. opencv-python이 없으면
전처리 없이 원본 이미지를 그대로 반환합니다(설치 안내는 README 참고).
"""
from PIL import Image


def preprocess(image: Image.Image) -> Image.Image:
    try:
        import cv2
        import numpy as np
    except ImportError:
        return image.convert("L")

    arr = np.array(image.convert("L"))

    # 이진화 후 기울어진 글자 영역의 최소 외접 사각형 각도로 deskew
    _, thresh = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    coords = cv2.findNonZero(thresh)
    angle = 0.0
    if coords is not None:
        rect = cv2.minAreaRect(coords)
        angle = rect[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

    if abs(angle) > 0.5:
        (h, w) = arr.shape
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        arr = cv2.warpAffine(arr, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    arr = cv2.adaptiveThreshold(
        arr, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
    )
    return Image.fromarray(arr)
