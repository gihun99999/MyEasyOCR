"""
Ollama 서버 연결 테스트
"""

import requests
import sys

def check_ollama():
    """Ollama 서버 상태 확인"""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Ollama 서버: 실행 중 (ON)")
            print(f"\n설치된 모델:")
            
            models = data.get('models', [])
            if models:
                for model in models:
                    print(f"  - {model['name']}")
                return True
            else:
                print("  ❌ 설치된 모델이 없습니다")
                print("\n모델 설치 방법:")
                print("  ollama pull mistral")
                return False
        else:
            print(f"❌ Ollama 서버 오류: HTTP {response.status_code}")
            return False
    
    except requests.exceptions.ConnectionError:
        print("❌ Ollama 서버 연결 실패")
        print("\nOllama 실행 방법:")
        print("  1. PowerShell에서: ollama serve")
        print("  2. 또는 Ollama 애플리케이션 실행")
        return False
    
    except requests.exceptions.Timeout:
        print("❌ Ollama 서버 타임아웃 (응답 없음)")
        return False
    
    except Exception as e:
        print(f"❌ 오류: {str(e)}")
        return False


if __name__ == "__main__":
    success = check_ollama()
    sys.exit(0 if success else 1)
