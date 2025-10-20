"""
OCR 프로그램 설정 파일
"""

import os
from pathlib import Path

# 기본 경로 설정
BASE_DIR = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / "images"
OUTPUT_DIR = BASE_DIR / "output"

# Ollama 설정
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "mistral"  # 또는 "llama2", "neural-chat" 등

# EasyOCR 설정
OCR_LANGUAGES = ['ko', 'en']  # 한글, 영어 지원
OCR_GPU = False  # GPU 사용 여부 (True면 GPU 사용, False면 CPU)

# 후처리 설정
CORRECTION_PROMPT_TEMPLATE = """다음은 OCR로 추출한 텍스트입니다. 문법 오류를 수정하고, 명확하지 않은 부분을 보정해주세요. 원본 의미는 보존하면서 자연스럽게 정정해주세요.

[원본 텍스트]
{text}

[정정된 텍스트]"""

# 로깅 설정
LOG_LEVEL = "INFO"
LOG_FILE = BASE_DIR / "ocr_program.log"

# 파일 저장 설정
SAVE_RAW_TEXT = True  # 원본 OCR 텍스트 저장
SAVE_CORRECTED_TEXT = True  # 정정된 텍스트 저장
SAVE_JSON_RESULT = True  # JSON 형식으로 결과 저장
