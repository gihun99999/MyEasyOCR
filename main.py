"""
EasyOCR + Ollama OCR 프로그램 메인 스크립트
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from ocr_engine import OCREngine
from llm_corrector import LLMCorrector
from config.config import (
    IMAGES_DIR, OUTPUT_DIR, OLLAMA_HOST, OLLAMA_MODEL,
    OCR_LANGUAGES, OCR_GPU, CORRECTION_PROMPT_TEMPLATE,
    LOG_LEVEL, LOG_FILE, SAVE_RAW_TEXT, SAVE_CORRECTED_TEXT, SAVE_JSON_RESULT
)


# 로깅 설정
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def setup_directories():
    """필요한 디렉토리 생성"""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("디렉토리 설정 완료")


def process_single_image(image_path: str, ocr_engine: OCREngine, llm_corrector: LLMCorrector) -> dict:
    """
    단일 이미지 처리 (OCR + 후처리)
    
    Args:
        image_path: 이미지 파일 경로
        ocr_engine: OCR 엔진 인스턴스
        llm_corrector: LLM 보정기 인스턴스
    
    Returns:
        처리 결과
    """
    try:
        logger.info(f"\n=== 이미지 처리 시작: {Path(image_path).name} ===")
        
        # 1. OCR 추출
        ocr_result = ocr_engine.extract_text(image_path)
        raw_text = ocr_result['full_text']
        
        logger.info(f"OCR 추출 완료 (신뢰도: {ocr_result['confidence_avg']:.2%})")
        logger.info(f"추출 텍스트:\n{raw_text}\n")
        
        # 2. LLM 후처리
        correction_result = llm_corrector.correct_text(raw_text, CORRECTION_PROMPT_TEMPLATE)
        corrected_text = correction_result['corrected_text']
        
        if correction_result['success']:
            logger.info(f"LLM 보정 완료")
            logger.info(f"보정된 텍스트:\n{corrected_text}\n")
        else:
            logger.warning(f"LLM 보정 실패: {correction_result.get('error')}")
            logger.warning("원본 텍스트를 사용합니다")
            corrected_text = raw_text
        
        # 결과 통합
        result = {
            'filename': Path(image_path).name,
            'timestamp': datetime.now().isoformat(),
            'ocr': {
                'raw_text': raw_text,
                'confidence': ocr_result['confidence_avg'],
                'word_count': ocr_result['num_words']
            },
            'correction': {
                'corrected_text': corrected_text,
                'success': correction_result['success'],
                'model': correction_result.get('model', 'unknown'),
                'error': correction_result.get('error')
            }
        }
        
        return result
    
    except Exception as e:
        logger.error(f"이미지 처리 중 오류: {str(e)}")
        return {
            'filename': Path(image_path).name,
            'error': str(e)
        }


def save_results(result: dict, base_filename: str):
    """
    처리 결과 저장
    
    Args:
        result: 처리 결과
        base_filename: 기본 파일명 (확장자 제외)
    """
    try:
        if 'error' in result:
            logger.warning(f"결과 저장 건너뜀 (오류 발생)")
            return
        
        # JSON 결과 저장
        if SAVE_JSON_RESULT:
            json_path = OUTPUT_DIR / f"{base_filename}_result.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info(f"JSON 결과 저장: {json_path}")
        
        # 원본 OCR 텍스트 저장
        if SAVE_RAW_TEXT:
            raw_path = OUTPUT_DIR / f"{base_filename}_raw.txt"
            with open(raw_path, 'w', encoding='utf-8') as f:
                f.write(result['ocr']['raw_text'])
            logger.info(f"원본 텍스트 저장: {raw_path}")
        
        # 보정된 텍스트 저장
        if SAVE_CORRECTED_TEXT:
            corrected_path = OUTPUT_DIR / f"{base_filename}_corrected.txt"
            with open(corrected_path, 'w', encoding='utf-8') as f:
                f.write(result['correction']['corrected_text'])
            logger.info(f"보정된 텍스트 저장: {corrected_path}")
    
    except Exception as e:
        logger.error(f"결과 저장 중 오류: {str(e)}")


def process_directory(image_dir: str = None):
    """
    디렉토리의 모든 이미지 처리
    
    Args:
        image_dir: 이미지 디렉토리 (기본값: IMAGES_DIR)
    """
    if image_dir is None:
        image_dir = IMAGES_DIR
    
    image_dir = Path(image_dir)
    
    if not image_dir.exists():
        logger.error(f"디렉토리가 없습니다: {image_dir}")
        return
    
    # OCR 엔진 초기화
    logger.info("OCR 엔진 초기화 중...")
    ocr_engine = OCREngine(OCR_LANGUAGES, OCR_GPU)
    
    # LLM 보정기 초기화
    logger.info("LLM 보정기 초기화 중...")
    llm_corrector = LLMCorrector(OLLAMA_HOST, OLLAMA_MODEL)
    
    # 이미지 파일 찾기
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'}
    image_files = [
        f for f in image_dir.iterdir()
        if f.suffix.lower() in image_extensions
    ]
    
    if not image_files:
        logger.warning(f"이미지 파일을 찾을 수 없습니다: {image_dir}")
        return
    
    logger.info(f"찾은 이미지 파일: {len(image_files)}개")
    
    # 이미지 처리
    all_results = []
    for i, image_file in enumerate(image_files, 1):
        logger.info(f"\n[{i}/{len(image_files)}]")
        result = process_single_image(str(image_file), ocr_engine, llm_corrector)
        all_results.append(result)
        
        # 개별 결과 저장
        base_name = image_file.stem
        save_results(result, base_name)
    
    # 전체 결과 저장
    summary_path = OUTPUT_DIR / f"batch_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    logger.info(f"\n전체 결과 저장: {summary_path}")
    
    # 통계
    logger.info("\n=== 처리 완료 ===")
    logger.info(f"총 처리 파일: {len(image_files)}개")
    successful = sum(1 for r in all_results if 'error' not in r)
    logger.info(f"성공: {successful}개, 실패: {len(image_files) - successful}개")


def test_single_image(image_path: str):
    """
    단일 이미지 테스트 처리
    
    Args:
        image_path: 이미지 파일 경로
    """
    logger.info("=== 단일 이미지 테스트 ===")
    
    ocr_engine = OCREngine(OCR_LANGUAGES, OCR_GPU)
    llm_corrector = LLMCorrector(OLLAMA_HOST, OLLAMA_MODEL)
    
    result = process_single_image(image_path, ocr_engine, llm_corrector)
    
    print("\n" + "="*50)
    print("처리 결과:")
    print("="*50)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import sys
    
    setup_directories()
    
    logger.info("OCR 프로그램 시작")
    logger.info(f"OCR 언어: {OCR_LANGUAGES}")
    logger.info(f"LLM 모델: {OLLAMA_MODEL}")
    logger.info(f"Ollama 호스트: {OLLAMA_HOST}")
    
    if len(sys.argv) > 1:
        # 특정 이미지 파일 처리
        image_path = sys.argv[1]
        if Path(image_path).exists():
            test_single_image(image_path)
        else:
            logger.error(f"파일을 찾을 수 없습니다: {image_path}")
    else:
        # 디렉토리 배치 처리
        process_directory()
