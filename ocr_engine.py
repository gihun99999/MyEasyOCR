"""
EasyOCR 기반 OCR 엔진
이미지에서 텍스트를 추출하는 기능 제공
"""

import logging
from typing import List, Dict, Any
import easyocr
from pathlib import Path
import numpy as np
import cv2

logger = logging.getLogger(__name__)


class OCREngine:
    """
    EasyOCR 기반 텍스트 추출 엔진
    """
    
    def __init__(self, languages: List[str] = None, gpu: bool = True):
        """
        OCR 엔진 초기화
        
        Args:
            languages: OCR 언어 리스트 (기본값: ['ko', 'en'])
            gpu: GPU 사용 여부
        """
        if languages is None:
            languages = ['ko', 'en']
        
        self.languages = languages
        self.gpu = gpu
        
        logger.info(f"OCR 엔진 초기화 중... (언어: {languages}, GPU: {gpu})")
        
        try:
            self.reader = easyocr.Reader(
                lang_list=languages,
                gpu=gpu,
                verbose=False
            )
            logger.info("OCR 엔진 초기화 완료")
        except Exception as e:
            logger.error(f"OCR 엔진 초기화 실패: {str(e)}")
            raise
    
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """
        이미지에서 텍스트 추출
        
        Args:
            image_path: 이미지 파일 경로
        
        Returns:
            OCR 결과 딕셔너리
            {
                'full_text': 전체 텍스트,
                'confidence_avg': 평균 신뢰도,
                'num_words': 단어 수,
                'details': 상세 결과 리스트
            }
        """
        try:
            # 파일 존재 확인
            if not Path(image_path).exists():
                raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
            
            logger.info(f"이미지 OCR 처리: {image_path}")
            
            # 한글 경로 지원을 위해 numpy를 사용하여 이미지 읽기
            # OpenCV는 한글 경로를 지원하지 않으므로 우회 방법 사용
            with open(image_path, 'rb') as f:
                image_data = np.frombuffer(f.read(), np.uint8)
                image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError(f"이미지를 읽을 수 없습니다: {image_path}")
            
            # OCR 실행 (numpy array 전달)
            results = self.reader.readtext(image)
            
            if not results:
                logger.warning("텍스트를 추출할 수 없습니다")
                return {
                    'full_text': '',
                    'confidence_avg': 0.0,
                    'num_words': 0,
                    'details': []
                }
            
            # 결과 처리
            texts = []
            confidences = []
            details = []
            
            for bbox, text, confidence in results:
                texts.append(text)
                confidences.append(confidence)
                details.append({
                    'bbox': bbox,
                    'text': text,
                    'confidence': confidence
                })
            
            # 전체 텍스트 결합
            full_text = ' '.join(texts)
            
            # 평균 신뢰도 계산
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            result = {
                'full_text': full_text,
                'confidence_avg': avg_confidence,
                'num_words': len(texts),
                'details': details
            }
            
            logger.info(f"OCR 완료 - 단어 수: {len(texts)}, 평균 신뢰도: {avg_confidence:.2%}")
            
            return result
        
        except Exception as e:
            logger.error(f"OCR 처리 중 오류: {str(e)}")
            raise
    
    def extract_text_batch(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """
        여러 이미지에서 텍스트 일괄 추출
        
        Args:
            image_paths: 이미지 파일 경로 리스트
        
        Returns:
            OCR 결과 리스트
        """
        results = []
        
        for image_path in image_paths:
            try:
                result = self.extract_text(image_path)
                results.append({
                    'filename': Path(image_path).name,
                    'success': True,
                    'result': result
                })
            except Exception as e:
                logger.error(f"이미지 처리 실패 ({image_path}): {str(e)}")
                results.append({
                    'filename': Path(image_path).name,
                    'success': False,
                    'error': str(e)
                })
        
        return results


if __name__ == "__main__":
    # 테스트 코드
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("사용법: python ocr_engine.py <이미지_파일_경로>")
        sys.exit(1)
    
    # OCR 엔진 생성
    engine = OCREngine(['ko', 'en'], gpu=False)
    
    # 텍스트 추출
    image_path = sys.argv[1]
    result = engine.extract_text(image_path)
    
    print("\n" + "="*50)
    print("OCR 결과:")
    print("="*50)
    print(f"추출된 텍스트: {result['full_text']}")
    print(f"평균 신뢰도: {result['confidence_avg']:.2%}")
    print(f"단어 수: {result['num_words']}")
