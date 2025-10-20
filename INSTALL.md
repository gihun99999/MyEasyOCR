"""
설치 및 실행 가이드
"""

# 📋 설치 순서

## 1단계: Ollama 설치 및 실행

### Windows / Mac / Linux 공통

1. **Ollama 다운로드**
   - 웹사이트: https://ollama.ai
   - 자신의 OS에 맞는 버전 다운로드

2. **설치 완료 후, 모델 다운로드**
   
   PowerShell (Windows) / Terminal (Mac/Linux):
   ```bash
   ollama pull mistral
   ```
   
   > 첫 다운로드 시 4GB 정도가 필요하며, 인터넷 속도에 따라 5~20분 소요됩니다.

3. **Ollama 서버 실행**
   ```bash
   ollama serve
   ```
   
   > 성공하면 "Listening on 127.0.0.1:11434" 메시지가 표시됩니다.


## 2단계: Python 패키지 설치

새로운 PowerShell 창을 열고 프로젝트 폴더에서:

```bash
pip install -r requirements.txt
```

또는 개별 설치 (선택사항):

```bash
pip install easyocr==1.7.0 pillow==10.1.0 requests==2.31.0
```

> ⚠️ EasyOCR도 첫 실행 시 약 1GB의 모델을 다운로드합니다.


## 3단계: 빠른 테스트 실행

```bash
python quickstart.py
```

이 스크립트는:
- ✓ 필수 패키지 확인
- ✓ Ollama 서버 연결 확인
- ✓ 테스트 이미지 생성
- ✓ OCR 프로그램 실행


## 4단계: 자신의 이미지로 처리

### 방법 1: 배치 처리 (권장)

1. `images/` 폴더에 이미지 파일 추가
2. 다음 명령어 실행:
   ```bash
   python main.py
   ```

### 방법 2: 단일 이미지 처리

```bash
python main.py "C:/path/to/image.png"
```


# 🎯 작동 원리

1. **EasyOCR 처리**
   - 이미지에서 텍스트 추출
   - 신뢰도 점수 계산
   - 줄 단위로 텍스트 정렬

2. **Ollama LLM 보정**
   - OCR 결과 텍스트를 Ollama로 전송
   - LLM이 오류 수정 및 문법 정정
   - 보정된 텍스트 반환

3. **결과 저장**
   - 원본 OCR 텍스트 (.txt)
   - 보정된 텍스트 (.txt)
   - 상세 결과 (JSON)


# 📂 폴더 구조

```
OCR Prog/
├── main.py                 # 메인 프로그램
├── quickstart.py           # 빠른 시작 스크립트
├── create_sample_image.py  # 테스트 이미지 생성
├── ocr_engine.py           # EasyOCR 엔진
├── llm_corrector.py        # Ollama LLM 보정기
├── requirements.txt        # Python 패키지 목록
├── README.md               # 프로젝트 설명서
│
├── config/
│   └── config.py           # 프로젝트 설정
│
├── images/                 # OCR 처리할 이미지 폴더
│   └── (여기에 이미지 파일 추가)
│
└── output/                 # 처리 결과 저장 폴더
    ├── *_result.json       # 상세 결과
    ├── *_raw.txt           # 원본 OCR 텍스트
    └── *_corrected.txt     # 보정된 텍스트
```


# ⚙️ 설정 커스터마이징

`config/config.py` 파일을 수정하여 다음을 조정할 수 있습니다:

### OCR 언어 변경
```python
OCR_LANGUAGES = ['ko', 'en']  # 한글, 영어
# 다른 언어: 'zh' (중국어), 'ja' (일본어), 'fr' (프랑스어) 등
```

### GPU 사용 (빠른 처리)
```python
OCR_GPU = True  # GPU가 있는 경우만 True
```

### LLM 모델 변경
```python
OLLAMA_MODEL = "mistral"  # mistral, llama2, neural-chat 등
```

### 보정 프롬프트 커스터마이징
```python
CORRECTION_PROMPT_TEMPLATE = """
다음 텍스트를 정정해주세요:
{text}
"""
```


# 🚀 고급 팁

## 1. 더 빠른 처리
- GPU 활용: `OCR_GPU = True`
- Mistral 모델 사용 (기본값)
- 이미지 해상도 낮추기

## 2. 더 정확한 인식
- 고해상도 이미지 사용
- 필요한 언어 모두 추가
- 프롬프트 최적화

## 3. 배치 처리 최적화
- 유사한 이미지끼리 묶기
- 큰 이미지는 사전에 축소
- 불필요한 로깅 비활성화

## 4. 커스텀 후처리
`llm_corrector.py`의 `correct_text()` 메소드에 전달하는 `prompt_template` 수정:

```python
from llm_corrector import LLMCorrector

corrector = LLMCorrector()
custom_prompt = """
다음 의료 기록을 정정하세요:
{text}
"""
result = corrector.correct_text(text, prompt_template=custom_prompt)
```


# 🔧 트러블슈팅

## "Ollama 서버에 연결할 수 없습니다"
- [ ] Ollama가 실행 중인지 확인 (ollama serve)
- [ ] 포트 11434가 다른 프로그램에서 사용 중이 아닌지 확인
- [ ] 방화벽 설정 확인

## "메모리 부족" 오류
- [ ] 이미지 크기 줄이기
- [ ] OCR_GPU = False로 설정
- [ ] 더 작은 모델 사용 (neural-chat)

## OCR 결과가 정확하지 않음
- [ ] 더 높은 해상도 이미지 사용
- [ ] 필요한 언어 추가
- [ ] 프롬프트 개선
- [ ] 이미지 전처리 (대비 조정 등)

## Ollama 모델 다운로드 오류
- [ ] 인터넷 연결 확인
- [ ] 디스크 공간 확인 (최소 4GB)
- [ ] 방화벽/프록시 설정 확인


# 📊 성능 비교

### 처리 시간 (약 500단어 기준)

| 항목 | 시간 |
|------|------|
| OCR (EasyOCR) | 2-5초 |
| LLM 보정 (Mistral) | 5-15초 |
| 총 처리 시간 | 7-20초 |

> GPU 사용 시 OCR 속도는 10배 이상 빨라집니다.

### 모델별 특성

| 모델 | 크기 | 속도 | 정확도 | 메모리 |
|------|------|------|--------|--------|
| mistral | 4.1GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 8GB |
| llama2 | 3.8GB | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 6GB |
| neural-chat | 3.9GB | ⭐⭐⭐⭐ | ⭐⭐⭐ | 7GB |


# 📝 라이선스 및 출처

- **EasyOCR**: Apache License 2.0 (https://github.com/JaidedAI/EasyOCR)
- **Ollama**: MIT License (https://github.com/ollama/ollama)
- **Pillow**: HPND License
- **Requests**: Apache License 2.0

---

✅ **모든 설정이 완료되었습니다!**

질문이 있으면 README.md를 참고하세요.
"""
