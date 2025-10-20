"""
Ollama를 사용한 LLM 기반 텍스트 보정
"""

import requests
import logging
import json
from typing import Dict, Any
import time

logger = logging.getLogger(__name__)


class LLMCorrector:
    """Ollama를 사용한 LLM 텍스트 보정"""
    
    def __init__(self, ollama_host: str = "http://localhost:11434", model: str = "mistral"):
        """
        LLM 보정기 초기화
        
        Args:
            ollama_host: Ollama 서버 주소
            model: 사용할 모델명
        """
        self.ollama_host = ollama_host.rstrip('/')
        self.model = model
        self.api_url = f"{self.ollama_host}/api/generate"
        
        # Ollama 서버 연결 확인
        if not self._check_connection():
            logger.warning(
                f"Ollama 서버에 연결할 수 없습니다.\n"
                f"1. Ollama 설치: https://ollama.ai\n"
                f"2. Ollama 실행: ollama serve\n"
                f"3. 모델 다운로드: ollama pull {model}"
            )
    
    def _check_connection(self) -> bool:
        """Ollama 서버 연결 확인"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def _wait_for_model(self, timeout: int = 30) -> bool:
        """
        모델이 준비될 때까지 대기
        
        Args:
            timeout: 최대 대기 시간 (초)
        
        Returns:
            모델 준비 완료 여부
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        return False
    
    def correct_text(self, text: str, prompt_template: str = None, max_retries: int = 3) -> Dict[str, Any]:
        """
        LLM을 사용한 텍스트 보정
        
        Args:
            text: 보정할 텍스트
            prompt_template: 커스텀 프롬프트 템플릿
            max_retries: 최대 재시도 횟수
        
        Returns:
            {
                'original_text': str,
                'corrected_text': str,
                'success': bool,
                'error': str (실패 시)
            }
        """
        if not text or not text.strip():
            return {
                'original_text': text,
                'corrected_text': '',
                'success': False,
                'error': '빈 텍스트'
            }
        
        # 기본 프롬프트
        if prompt_template is None:
            prompt_template = """다음은 OCR로 추출한 텍스트입니다. 다음 작업을 수행해주세요:
1. OCR 오류로 인한 문자 치환 수정
2. 자연스럽지 않은 표현 정정
3. 띄어쓰기 및 문법 오류 수정
4. 원본의 의미는 최대한 보존

[원본 텍스트]
{text}

[정정된 텍스트만 출력]"""
        
        prompt = prompt_template.format(text=text)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"LLM 보정 시작 (시도: {attempt + 1}/{max_retries})")
                
                response = requests.post(
                    self.api_url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": 0.3  # 낮은 온도로 일관성 있는 결과
                    },
                    timeout=120  # 2분 타임아웃
                )
                
                if response.status_code == 200:
                    result = response.json()
                    corrected_text = result.get('response', '').strip()
                    
                    logger.info(f"LLM 보정 완료")
                    
                    return {
                        'original_text': text,
                        'corrected_text': corrected_text,
                        'success': True,
                        'model': self.model
                    }
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.warning(f"LLM 요청 실패: {error_msg}")
                    
                    if attempt == max_retries - 1:
                        return {
                            'original_text': text,
                            'corrected_text': text,
                            'success': False,
                            'error': error_msg
                        }
            
            except requests.exceptions.Timeout:
                logger.warning(f"LLM 요청 타임아웃 (시도: {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    return {
                        'original_text': text,
                        'corrected_text': text,
                        'success': False,
                        'error': '요청 타임아웃'
                    }
            
            except requests.exceptions.ConnectionError:
                logger.error(
                    f"Ollama 서버에 연결할 수 없습니다.\n"
                    f"Ollama 서버를 실행해주세요: ollama serve"
                )
                return {
                    'original_text': text,
                    'corrected_text': text,
                    'success': False,
                    'error': 'Ollama 서버 연결 불가'
                }
            
            except Exception as e:
                logger.error(f"LLM 보정 중 오류: {str(e)}")
                if attempt == max_retries - 1:
                    return {
                        'original_text': text,
                        'corrected_text': text,
                        'success': False,
                        'error': str(e)
                    }
            
            time.sleep(1)  # 재시도 전 대기
        
        return {
            'original_text': text,
            'corrected_text': text,
            'success': False,
            'error': '최대 재시도 횟수 초과'
        }
    
    def batch_correct(self, texts: list, prompt_template: str = None) -> list:
        """
        여러 텍스트 일괄 보정
        
        Args:
            texts: 보정할 텍스트 리스트
            prompt_template: 커스텀 프롬프트 템플릿
        
        Returns:
            보정 결과 리스트
        """
        results = []
        for i, text in enumerate(texts, 1):
            logger.info(f"배치 처리 중... {i}/{len(texts)}")
            result = self.correct_text(text, prompt_template)
            results.append(result)
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Ollama 모델 정보 조회"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                return response.json()
            return {'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'error': str(e)}
