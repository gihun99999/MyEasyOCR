"""
GUI 애플리케이션 실행 스크립트
"""

import subprocess
import sys
import os
from pathlib import Path

def check_and_install_dependencies():
    """필수 패키지 확인 및 설치"""
    print("=" * 60)
    print("필수 패키지 확인 중...")
    print("=" * 60)
    
    required_packages = {
        'PyQt6': 'PyQt6',
        'easyocr': 'easyocr',
        'PIL': 'pillow',
        'cv2': 'opencv-python',
        'requests': 'requests'
    }
    
    missing = []
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✓ {package_name}")
        except ImportError:
            print(f"✗ {package_name} (설치 필요)")
            missing.append(package_name)
    
    if missing:
        print(f"\n{len(missing)}개 패키지를 설치하시겠습니까? (y/n): ", end='')
        if input().lower() == 'y':
            print("\n패키지 설치 중...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✓ 설치 완료!")
        else:
            print("필요한 패키지를 먼저 설치하세요:")
            print("  pip install -r requirements.txt")
            return False
    
    return True


def main():
    # 필수 패키지 확인
    if not check_and_install_dependencies():
        sys.exit(1)
    
    # GUI 앱 실행
    print("\nGUI 애플리케이션 시작 중...")
    from gui_app import main as run_gui_app
    run_gui_app()


if __name__ == "__main__":
    main()
