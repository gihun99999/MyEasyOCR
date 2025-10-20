"""
EasyOCR을 사용한 OCR 엔진
"""

import easyocr
import logging
from pathlib import Path
from typing import List, Dict, Any
from PIL import Image
import cv2

logger = logging.getLogger(__name__)


class OCREngine:
    """EasyOCR 기반 OCR 엔진"""
    
    def __init__(self, languages: List[str], gpu: bool = False):
        """
        OCR 엔진 초기화
        
        Args:
            languages: OCR 인식 언어 목록 (예: ['ko', 'en'])
            gpu: GPU 사용 여부
        """
        logger.info(f"OCR 엔진 초기화 중... 언어: {languages}, GPU: {gpu}")
        self.reader = easyocr.Reader(languages, gpu=gpu)
        logger.info("OCR 엔진 초기화 완료")
    
    def extract_text(self, image_path: str, confidence_threshold: float = 0.5) -> Dict[str, Any]:
        """
        이미지에서 텍스트 추출
        
        Args:
            image_path: 이미지 파일 경로
            confidence_threshold: 신뢰도 임계값 (0~1)
        
        Returns:
            {
                'full_text': str,  # 전체 텍스트
                'detailed_results': List,  # 상세 결과
                'confidence_avg': float  # 평균 신뢰도
            }
        """
        try:
            logger.info(f"이미지 OCR 처리: {image_path}")
            
            # 이미지 읽기
            if not Path(image_path).exists():
                raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
            
            # EasyOCR 처리
            results = self.reader.readtext(image_path, detail=1)
            
            # 신뢰도 필터링
            filtered_results = [
                result for result in results 
                if result[2] >= confidence_threshold
            ]
            
            # 텍스트 추출 및 정렬
            full_text = self._format_text(filtered_results)
            confidence_values = [result[2] for result in filtered_results]
            confidence_avg = sum(confidence_values) / len(confidence_values) if confidence_values else 0
            
            logger.info(f"OCR 완료 - 신뢰도: {confidence_avg:.2%}")
            
            return {
                'full_text': full_text,
                'detailed_results': filtered_results,
                'confidence_avg': confidence_avg,
                'num_words': len(filtered_results)
            }
        
        except Exception as e:
            logger.error(f"OCR 처리 중 오류: {str(e)}")
            raise
    
    def _format_text(self, results: List) -> str:
        """
        OCR 결과를 텍스트로 포맷팅
        
        Args:
            results: EasyOCR의 상세 결과
        
        Returns:
            포맷된 텍스트
        """
        lines = []
        current_y = 0
        current_line_texts = []
        
        # Y 좌표로 정렬 (위에서 아래로)
        sorted_results = sorted(results, key=lambda x: x[0][0][1])
        
        for result in sorted_results:
            text = result[1]
            bbox = result[0]
            
            # Y 좌표 추출 (위쪽)
            y_coord = bbox[0][1]
            
            # 새로운 줄 감지 (Y 차이 > 10)
            if current_line_texts and abs(y_coord - current_y) > 10:
                lines.append(' '.join(current_line_texts))
                current_line_texts = []
            
            current_line_texts.append(text)
            current_y = y_coord
        
        # 마지막 줄 추가
        if current_line_texts:
            lines.append(' '.join(current_line_texts))
        
        return '\n'.join(lines)
    
    def extract_from_multiple_images(self, image_dir: str) -> Dict[str, Any]:
        """
        디렉토리의 모든 이미지에서 텍스트 추출
        
        Args:
            image_dir: 이미지 디렉토리 경로
        
        Returns:
            {filename: 추출 결과}
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'}
        image_dir = Path(image_dir)
        
        results = {}
        for image_file in image_dir.iterdir():
            if image_file.suffix.lower() in image_extensions:
                try:
                    results[image_file.name] = self.extract_text(str(image_file))
                except Exception as e:
                    logger.error(f"파일 처리 실패 - {image_file.name}: {str(e)}")
                    results[image_file.name] = {'error': str(e)}
        
        return results
