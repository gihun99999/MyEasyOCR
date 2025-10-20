"""
빠른 시작 가이드 및 테스트 스크립트
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_requirements():
    """필수 요구사항 확인"""
    print("=" * 60)
    print("필수 요구사항 확인")
    print("=" * 60)
    
    # Python 버전 확인
    print(f"✓ Python {sys.version.split()[0]}")
    
    # 패키지 확인
    packages = ['easyocr', 'PIL', 'requests', 'cv2']
    missing_packages = []
    
    for package in packages:
        try:
            __import__(package)
            print(f"✓ {package} 설치됨")
        except ImportError:
            print(f"✗ {package} 미설치")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n패키지 설치 필요: {', '.join(missing_packages)}")
        print("다음 명령어를 실행하세요:")
        print("  pip install -r requirements.txt")
        return False
    
    return True


def check_ollama():
    """Ollama 서버 확인"""
    print("\n" + "=" * 60)
    print("Ollama 서버 확인")
    print("=" * 60)
    
    import requests
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            print("✓ Ollama 서버 실행 중")
            
            models = response.json().get('models', [])
            if models:
                print(f"✓ 설치된 모델: {len(models)}개")
                for model in models:
                    print(f"  - {model['name']}")
                return True
            else:
                print("✗ 설치된 모델이 없습니다")
                print("\n모델 설치 방법:")
                print("  ollama pull mistral")
                return False
    except requests.exceptions.ConnectionError:
        print("✗ Ollama 서버가 실행 중이 아닙니다")
        print("\nOllama 실행 방법:")
        if platform.system() == "Windows":
            print("  1. Ollama 애플리케이션 실행 (설치되어 있다면)")
            print("  2. 또는 PowerShell에서: ollama serve")
        else:
            print("  터미널에서 다음 명령어 실행: ollama serve")
        return False
    except Exception as e:
        print(f"✗ Ollama 확인 중 오류: {e}")
        return False


def setup_directories():
    """디렉토리 생성"""
    print("\n" + "=" * 60)
    print("디렉토리 설정")
    print("=" * 60)
    
    dirs = ['images', 'output', 'config']
    for dir_name in dirs:
        dir_path = Path(dir_name)
        dir_path.mkdir(exist_ok=True)
        print(f"✓ {dir_path} 디렉토리 준비 완료")


def create_test_image():
    """테스트 이미지 생성"""
    print("\n" + "=" * 60)
    print("테스트 이미지 생성")
    print("=" * 60)
    
    try:
        from create_sample_image import create_sample_image
        create_sample_image("images/sample_ocr_test.png")
        print("✓ 테스트 이미지 생성 완료: images/sample_ocr_test.png")
        return True
    except Exception as e:
        print(f"✗ 테스트 이미지 생성 실패: {e}")
        return False


def run_main_program():
    """메인 프로그램 실행"""
    print("\n" + "=" * 60)
    print("OCR 프로그램 실행")
    print("=" * 60)
    
    try:
        print("\n메인 프로그램을 실행합니다...")
        print("이 과정은 시간이 걸릴 수 있습니다.\n")
        
        os.system("python main.py")
        return True
    except Exception as e:
        print(f"✗ 프로그램 실행 중 오류: {e}")
        return False


def main():
    """메인 함수"""
    print("\n" + "=" * 60)
    print("EasyOCR + Ollama 빠른 시작 가이드")
    print("=" * 60)
    
    # 1. 요구사항 확인
    if not check_requirements():
        print("\n❌ 필수 패키지가 없습니다. 설치 후 다시 실행하세요.")
        return
    
    # 2. Ollama 확인
    if not check_ollama():
        print("\n❌ Ollama를 설정하고 다시 실행하세요.")
        return
    
    # 3. 디렉토리 설정
    setup_directories()
    
    # 4. 테스트 이미지 생성
    image_created = create_test_image()
    
    # 5. 프로그램 실행
    if image_created:
        print("\n" + "=" * 60)
        print("준비 완료!")
        print("=" * 60)
        print("\n다음 단계:")
        print("1. images/ 폴더에 OCR할 이미지를 추가하세요")
        print("2. 다음 명령어로 프로그램을 실행하세요:")
        print("   python main.py")
        print("\n또는 지금 테스트 이미지로 실행:")
        
        response = input("\n테스트를 실행하시겠습니까? (y/n): ").strip().lower()
        if response == 'y':
            run_main_program()


if __name__ == "__main__":
    main()
