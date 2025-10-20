# EasyOCR + Ollama OCR 프로그램

OCR(광학 문자 인식)을 통해 이미지에서 텍스트를 추출하고, LLM을 사용하여 자동으로 오류를 보정하는 프로그램입니다.

**v2.0 (GUI 버전)** - 사용자 친화적인 그래픽 인터페이스 추가

## 주요 기능

- **GUI 인터페이스** ⭐ (새로운!)
  - 이미지 파일 선택 및 미리보기
  - 실시간 진행 상황 표시
  - 클립보드에 텍스트 복사 기능
  - 통계 정보 표시
  
- **EasyOCR**: 고정확도의 OCR 처리 (한글, 영어 등 다국어 지원)
- **Ollama LLM**: 로컬에서 실행되는 무료 LLM으로 OCR 오류 자동 보정
- **배치 처리**: 디렉토리의 여러 이미지 일괄 처리
- **결과 저장**: 원본 텍스트, 보정된 텍스트, JSON 형식으로 저장

## 설치 방법

### 1. Ollama 설치 및 실행

**Windows/Mac/Linux:**
1. [Ollama 공식 사이트](https://ollama.ai)에서 다운로드
2. 설치 완료 후, 터미널/PowerShell에서 다음 명령어 실행:

```bash
ollama pull mistral
ollama serve
```

> 첫 실행 시 모델 다운로드에 시간이 소요될 수 있습니다 (인터넷 속도에 따라 5~30분)

### 2. Python 패키지 설치

```bash
pip install -r requirements.txt
```

또는 개별 설치:

```bash
pip install easyocr pillow requests python-dotenv opencv-python PyQt6
```

> **주의**: EasyOCR 첫 실행 시 모델 다운로드에 시간이 걸릴 수 있습니다.

## 사용 방법 (v2.0)

### 💻 GUI 모드 (권장)

```bash
python run_gui.py
```

**주요 기능:**
1. "파일 선택" 버튼으로 OCR 처리할 이미지 선택
2. 이미지 미리보기 확인
3. 설정 조정 (언어, GPU, LLM 모델 등)
4. "OCR 처리 시작" 버튼으로 처리 시작
5. 결과 탭에서 원본/보정된 텍스트 확인
6. 텍스트 복사 또는 결과 저장

### 📋 배치 처리 모드

1. `images/` 폴더에 OCR을 처리할 이미지 파일을 저장
2. 다음 명령어 실행:

```bash
python main.py
```

3. 처리 결과는 `output/` 폴더에 저장됩니다

### 단일 이미지 처리

```bash
python main.py "path/to/image.png"
```

## 설정 변경

`config/config.py` 파일에서 다음을 설정할 수 있습니다:

```python
# OCR 언어 설정
OCR_LANGUAGES = ['ko', 'en']  # 한글, 영어

# GPU 사용 여부 (GPU가 있으면 True)
OCR_GPU = False

# Ollama 모델 선택
OLLAMA_MODEL = "mistral"  # mistral, llama2, neural-chat 등

# 결과 저장 옵션
SAVE_RAW_TEXT = True  # 원본 OCR 텍스트 저장
SAVE_CORRECTED_TEXT = True  # 보정된 텍스트 저장
SAVE_JSON_RESULT = True  # JSON 형식 저장
```

## 지원하는 Ollama 모델

| 모델 | 크기 | 속도 | 정확도 | 추천 |
|------|------|------|--------|------|
| mistral | 4.1GB | 빠름 | 높음 | ⭐⭐⭐⭐⭐ |
| llama2 | 3.8GB | 보통 | 높음 | ⭐⭐⭐⭐ |
| neural-chat | 3.9GB | 빠름 | 중간 | ⭐⭐⭐ |
| dolphin-mixtral | 26GB | 느림 | 매우높음 | ⭐⭐⭐⭐⭐ (고사양) |

다른 모델 받기:
```bash
ollama pull llama2
ollama pull neural-chat
ollama pull dolphin-mixtral
```

## 출력 파일

처리 후 `output/` 폴더에 다음 파일이 생성됩니다:

```
output/
├── image_name_result.json      # 전체 결과 (JSON)
├── image_name_raw.txt          # 원본 OCR 텍스트
├── image_name_corrected.txt    # LLM으로 보정된 텍스트
└── batch_result_YYYYMMDD_HHMMSS.json  # 배치 전체 결과
```

### JSON 형식 예시

```json
{
  "filename": "document.png",
  "timestamp": "2024-01-15T10:30:45.123456",
  "ocr": {
    "raw_text": "추출된 텍스트...",
    "confidence": 0.95,
    "word_count": 150
  },
  "correction": {
    "corrected_text": "보정된 텍스트...",
    "success": true,
    "model": "mistral",
    "error": null
  }
}
```

## 트러블슈팅

### "Ollama 서버에 연결할 수 없습니다" 오류

- Ollama가 실행 중인지 확인
- 터미널에서 `ollama serve` 명령어 실행
- 포트 11434가 사용 중이지 않은지 확인

### EasyOCR이 느리거나 메모리 부족

- GPU가 있으면 `config.py`에서 `OCR_GPU = True`로 설정
- 이미지 크기를 줄이거나 해상도 낮추기

### OCR 결과가 정확하지 않음

- 이미지 품질 개선 (명확하고 선명한 이미지 사용)
- `OCR_LANGUAGES`에 필요한 언어 모두 추가
- LLM 프롬프트 수정 (config.py의 `CORRECTION_PROMPT_TEMPLATE`)

## 성능 팁

1. **배치 처리**: 여러 이미지는 `main.py` (배치 모드)로 처리
2. **GPU 활용**: GPU가 있으면 `OCR_GPU = True`로 설정하면 10배 빨라짐
3. **모델 선택**: Mistral이 속도와 정확도 가장 좋음
4. **프롬프트 최적화**: 원하는 보정 방식에 맞게 프롬프트 수정

## 라이선스

- EasyOCR: Apache License 2.0
- Ollama: MIT License

## 참고

- [EasyOCR 문서](https://github.com/JaidedAI/EasyOCR)
- [Ollama 공식 사이트](https://ollama.ai)
