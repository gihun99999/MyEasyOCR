"""
테스트 용 샘플 이미지 생성 스크립트
"""

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

def create_sample_image(output_path: str = "images/sample_ocr_test.png"):
    """
    OCR 테스트용 샘플 이미지 생성
    
    Args:
        output_path: 저장할 이미지 경로
    """
    # 이미지 생성 (흰색 배경)
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # 기본 폰트 (시스템 폰트)
    try:
        font_large = ImageFont.truetype("arial.ttf", 40)
        font_medium = ImageFont.truetype("arial.ttf", 30)
        font_small = ImageFont.truetype("arial.ttf", 20)
    except:
        # 폰트가 없으면 기본 폰트 사용
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # 텍스트 그리기
    text_lines = [
        ("OCR 테스트 문서", font_large, (50, 50), (0, 0, 0)),
        ("", None, None, None),
        ("안녕하세요. 이것은 광학 문자 인식 테스트 문서입니다.", font_medium, (50, 150), (0, 0, 0)),
        ("This is a sample OCR test document.", font_medium, (50, 200), (0, 0, 0)),
        ("", None, None, None),
        ("주요 기능:", font_medium, (50, 280), (0, 0, 0)),
        ("1. EasyOCR을 사용한 이미지 텍스트 추출", font_small, (70, 330), (50, 50, 50)),
        ("2. Ollama LLM을 사용한 자동 보정", font_small, (70, 370), (50, 50, 50)),
        ("3. 배치 처리 지원", font_small, (70, 410), (50, 50, 50)),
        ("", None, None, None),
        ("처리 결과는 output 폴더에 저장됩니다.", font_medium, (50, 480), (0, 100, 0)),
    ]
    
    for text, font, pos, color in text_lines:
        if text and font:
            draw.text(pos, text, font=font, fill=color)
    
    # 이미지 저장
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    img.save(output_path)
    print(f"샘플 이미지 생성 완료: {output_path}")


if __name__ == "__main__":
    create_sample_image()
