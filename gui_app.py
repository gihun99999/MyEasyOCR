"""
EasyOCR + Ollama GUI 애플리케이션
PyQt6를 사용한 사용자 인터페이스
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from enum import Enum

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QLineEdit, QComboBox, QCheckBox,
    QSpinBox, QFileDialog, QProgressBar, QTabWidget, QTableWidget,
    QTableWidgetItem, QSplitter, QMessageBox, QStatusBar, QGroupBox,
    QFormLayout, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QColor, QFont, QTextCursor
from PyQt6.QtCore import QSize

from ocr_engine import OCREngine
from llm_corrector import LLMCorrector
from config.config import (
    OLLAMA_HOST, OLLAMA_MODEL, OCR_LANGUAGES,
    OCR_GPU, CORRECTION_PROMPT_TEMPLATE, OUTPUT_DIR, IMAGES_DIR
)


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProcessStatus(Enum):
    """처리 상태"""
    IDLE = "대기중"
    LOADING_MODELS = "모델 로딩 중..."
    PROCESSING_OCR = "OCR 처리 중..."
    PROCESSING_LLM = "LLM 보정 중..."
    COMPLETED = "완료"
    ERROR = "오류 발생"


class OCRWorker(QThread):
    """OCR 처리 스레드"""
    
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, image_path: str, ocr_engine: OCREngine, 
                 llm_corrector: LLMCorrector, enable_correction: bool = True):
        super().__init__()
        self.image_path = image_path
        self.ocr_engine = ocr_engine
        self.llm_corrector = llm_corrector
        self.enable_correction = enable_correction
    
    def run(self):
        try:
            # OCR 처리
            self.progress.emit("OCR 처리 중...")
            logger.info(f"이미지 OCR 처리: {self.image_path}")
            
            # 별도 스레드에서 OCR 실행 (메인 스레드 차단 방지)
            try:
                ocr_result = self.ocr_engine.extract_text(self.image_path)
                raw_text = ocr_result['full_text']
            except Exception as ocr_error:
                logger.error(f"OCR 처리 오류: {str(ocr_error)}")
                raise
            
            result = {
                'filename': Path(self.image_path).name,
                'timestamp': datetime.now().isoformat(),
                'ocr': {
                    'raw_text': raw_text,
                    'confidence': ocr_result['confidence_avg'],
                    'word_count': ocr_result['num_words']
                },
                'correction': None
            }
            
            # LLM 보정 (활성화된 경우)
            if self.enable_correction:
                self.progress.emit("LLM 보정 중...")
                logger.info("LLM 보정 처리")
                
                try:
                    correction_result = self.llm_corrector.correct_text(
                        raw_text, 
                        CORRECTION_PROMPT_TEMPLATE
                    )
                    
                    result['correction'] = {
                        'corrected_text': correction_result['corrected_text'],
                        'success': correction_result['success'],
                        'model': correction_result.get('model', 'unknown'),
                        'error': correction_result.get('error')
                    }
                except Exception as llm_error:
                    logger.error(f"LLM 보정 오류: {str(llm_error)}")
                    result['correction'] = {
                        'corrected_text': raw_text,
                        'success': False,
                        'model': OLLAMA_MODEL,
                        'error': str(llm_error)
                    }
            
            self.progress.emit("완료")
            self.finished.emit(result)
        
        except Exception as e:
            logger.error(f"처리 중 오류: {str(e)}")
            self.error.emit(str(e))


class OCRGuiApp(QMainWindow):
    """OCR GUI 애플리케이션 메인 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OCR 텍스트 추출 및 보정 도구")
        self.setGeometry(100, 100, 1200, 800)
        
        # 엔진 초기화
        self.ocr_engine = None
        self.llm_corrector = None
        self.current_image_path = None
        self.current_result = None
        self.worker = None
        
        # 상태바 설정 (UI보다 먼저)
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        # UI 구성
        self.setup_ui()
        
        # 엔진 초기화
        self.init_engines()
        self.update_status(ProcessStatus.IDLE)
    
    def setup_ui(self):
        """UI 구성"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 왼쪽: 컨트롤 패널
        left_panel = self.create_control_panel()
        
        # 오른쪽: 결과 표시
        right_panel = self.create_result_panel()
        
        # 스플리터로 나누기
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 850])
        
        main_layout.addWidget(splitter)
    
    def create_control_panel(self) -> QWidget:
        """컨트롤 패널 생성"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # 제목
        title = QLabel("OCR 도구")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # 이미지 선택
        layout.addWidget(QLabel("1. 이미지 선택"))
        
        image_button_layout = QHBoxLayout()
        self.image_path_label = QLineEdit()
        self.image_path_label.setReadOnly(True)
        self.image_path_label.setPlaceholderText("이미지 파일을 선택하세요...")
        
        browse_button = QPushButton("파일 선택")
        browse_button.clicked.connect(self.select_image)
        
        image_button_layout.addWidget(self.image_path_label)
        image_button_layout.addWidget(browse_button)
        layout.addLayout(image_button_layout)
        
        # 이미지 미리보기
        self.image_preview = QLabel()
        self.image_preview.setMinimumHeight(150)
        self.image_preview.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(QLabel("이미지 미리보기"))
        layout.addWidget(self.image_preview)
        
        # 설정
        layout.addSpacing(20)
        layout.addWidget(QLabel("2. 설정"))
        
        settings_group = QGroupBox("OCR 설정")
        settings_layout = QFormLayout()
        
        # OCR 언어
        self.language_combo = QComboBox()
        self.language_combo.addItems(["한글+영어", "한글만", "영어만", "한글+영어+중국어"])
        self.language_combo.setCurrentText("한글+영어")
        settings_layout.addRow("언어:", self.language_combo)
        
        # GPU 사용
        self.gpu_checkbox = QCheckBox("GPU 사용 (빠른 처리)")
        self.gpu_checkbox.setChecked(OCR_GPU)
        settings_layout.addRow(self.gpu_checkbox)
        
        # 신뢰도 임계값
        self.confidence_spinbox = QSpinBox()
        self.confidence_spinbox.setRange(0, 100)
        self.confidence_spinbox.setValue(50)
        self.confidence_spinbox.setSuffix("%")
        settings_layout.addRow("신뢰도 임계값:", self.confidence_spinbox)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # LLM 설정
        layout.addSpacing(10)
        llm_group = QGroupBox("LLM 보정 설정")
        llm_layout = QFormLayout()
        
        # 보정 활성화
        self.correction_checkbox = QCheckBox("LLM 보정 활성화")
        self.correction_checkbox.setChecked(True)
        llm_layout.addRow(self.correction_checkbox)
        
        # LLM 모델
        self.model_combo = QComboBox()
        self.model_combo.addItems(["mistral", "llama2", "neural-chat"])
        self.model_combo.setCurrentText(OLLAMA_MODEL)
        llm_layout.addRow("모델:", self.model_combo)
        
        llm_group.setLayout(llm_layout)
        layout.addWidget(llm_group)
        
        # 처리 버튼
        layout.addSpacing(20)
        self.process_button = QPushButton("OCR 처리 시작")
        self.process_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.process_button.clicked.connect(self.start_processing)
        layout.addWidget(self.process_button)
        
        # 진행률 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 상태 메시지
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-size: 10pt;")
        layout.addWidget(self.status_label)
        
        # 결과 저장
        layout.addSpacing(20)
        layout.addWidget(QLabel("3. 결과 저장"))
        
        save_layout = QHBoxLayout()
        
        self.save_button = QPushButton("결과 저장")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_result)
        
        self.export_button = QPushButton("내보내기")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_result)
        
        save_layout.addWidget(self.save_button)
        save_layout.addWidget(self.export_button)
        layout.addLayout(save_layout)
        
        # 확장 공간
        layout.addStretch()
        
        return panel
    
    def create_result_panel(self) -> QWidget:
        """결과 표시 패널 생성"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # 탭 위젯
        self.tabs = QTabWidget()
        
        # 탭 1: 원본 OCR 텍스트
        self.raw_text_edit = QTextEdit()
        self.raw_text_edit.setReadOnly(True)
        self.tabs.addTab(self.raw_text_edit, "원본 OCR 텍스트")
        
        # 탭 2: 보정된 텍스트
        self.corrected_text_edit = QTextEdit()
        self.corrected_text_edit.setReadOnly(True)
        self.tabs.addTab(self.corrected_text_edit, "보정된 텍스트")
        
        # 탭 3: 통계 정보
        self.stats_text_edit = QTextEdit()
        self.stats_text_edit.setReadOnly(True)
        self.tabs.addTab(self.stats_text_edit, "통계 정보")
        
        layout.addWidget(self.tabs)
        
        # 복사 버튼
        copy_layout = QHBoxLayout()
        
        self.copy_raw_button = QPushButton("원본 복사")
        self.copy_raw_button.setEnabled(False)
        self.copy_raw_button.clicked.connect(self.copy_raw_text)
        
        self.copy_corrected_button = QPushButton("보정 텍스트 복사")
        self.copy_corrected_button.setEnabled(False)
        self.copy_corrected_button.clicked.connect(self.copy_corrected_text)
        
        copy_layout.addWidget(self.copy_raw_button)
        copy_layout.addWidget(self.copy_corrected_button)
        copy_layout.addStretch()
        
        layout.addLayout(copy_layout)
        
        return panel
    
    def init_engines(self):
        """OCR 엔진 및 LLM 초기화"""
        try:
            self.update_status(ProcessStatus.LOADING_MODELS)
            self.status_label.setText("모델을 로딩 중입니다. 잠시만 기다려주세요...")
            
            logger.info("OCR 엔진 초기화 중...")
            self.ocr_engine = OCREngine(OCR_LANGUAGES, OCR_GPU)
            
            logger.info("LLM 보정기 초기화 중...")
            self.llm_corrector = LLMCorrector(OLLAMA_HOST, self.model_combo.currentText())
            
            self.update_status(ProcessStatus.IDLE)
            self.status_label.setText("준비 완료!")
        
        except Exception as e:
            logger.error(f"엔진 초기화 오류: {str(e)}")
            self.update_status(ProcessStatus.ERROR)
            self.status_label.setText(f"초기화 오류: {str(e)}")
            QMessageBox.critical(self, "초기화 오류", f"엔진 초기화 중 오류가 발생했습니다:\n{str(e)}")
    
    def select_image(self):
        """이미지 파일 선택"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "이미지 선택", str(IMAGES_DIR),
            "이미지 파일 (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;모든 파일 (*.*)"
        )
        
        if file_path:
            self.current_image_path = file_path
            self.image_path_label.setText(file_path)
            
            # 이미지 미리보기
            self.show_image_preview(file_path)
            
            # 결과 초기화
            self.clear_results()
    
    def show_image_preview(self, image_path: str):
        """이미지 미리보기 표시"""
        try:
            pixmap = QPixmap(image_path)
            
            # 크기 조정
            max_width = 300
            max_height = 150
            
            if pixmap.width() > max_width or pixmap.height() > max_height:
                pixmap = pixmap.scaledToFit(
                    max_width, max_height,
                    Qt.AspectRatioMode.KeepAspectRatio
                )
            
            self.image_preview.setPixmap(pixmap)
        except Exception as e:
            logger.error(f"미리보기 오류: {str(e)}")
            self.image_preview.setText("미리보기 불가")
    
    def start_processing(self):
        """OCR 처리 시작"""
        if not self.current_image_path:
            QMessageBox.warning(self, "경고", "이미지를 선택하세요.")
            return
        
        if not Path(self.current_image_path).exists():
            QMessageBox.warning(self, "경고", "이미지 파일을 찾을 수 없습니다.")
            return
        
        # 결과 초기화
        self.clear_results()
        
        # 처리 버튼 비활성화
        self.process_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 워커 스레드 시작
        self.worker = OCRWorker(
            self.current_image_path,
            self.ocr_engine,
            self.llm_corrector,
            self.correction_checkbox.isChecked()
        )
        
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.error.connect(self.on_processing_error)
        
        self.worker.start()
        
        self.update_status(ProcessStatus.PROCESSING_OCR)
    
    def on_progress(self, message: str):
        """진행 상황 업데이트"""
        self.status_label.setText(message)
        self.progress_bar.setValue(self.progress_bar.value() + 30)
    
    def on_processing_finished(self, result: dict):
        """처리 완료"""
        self.current_result = result
        
        # 결과 표시
        raw_text = result['ocr']['raw_text']
        self.raw_text_edit.setText(raw_text)
        
        if result['correction'] and result['correction']['success']:
            corrected_text = result['correction']['corrected_text']
            self.corrected_text_edit.setText(corrected_text)
            self.copy_corrected_button.setEnabled(True)
        else:
            self.corrected_text_edit.setText("보정 실패: " + (result['correction'].get('error', '알 수 없는 오류') if result['correction'] else "보정이 비활성화됨"))
            self.copy_corrected_button.setEnabled(False)
        
        # 통계 정보
        self.show_statistics(result)
        
        # 상태 업데이트
        self.progress_bar.setValue(100)
        self.update_status(ProcessStatus.COMPLETED)
        self.status_label.setText("처리 완료!")
        
        # 버튼 활성화
        self.process_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.export_button.setEnabled(True)
        self.copy_raw_button.setEnabled(True)
        
        QMessageBox.information(self, "완료", "OCR 처리가 완료되었습니다!")
    
    def on_processing_error(self, error_message: str):
        """처리 오류"""
        self.update_status(ProcessStatus.ERROR)
        self.status_label.setText(f"오류: {error_message}")
        self.progress_bar.setVisible(False)
        self.process_button.setEnabled(True)
        
        QMessageBox.critical(self, "오류", f"처리 중 오류가 발생했습니다:\n{error_message}")
    
    def show_statistics(self, result: dict):
        """통계 정보 표시"""
        stats_text = f"""
=== OCR 통계 ===

파일명: {result['filename']}
처리 시간: {result['timestamp']}

OCR 결과:
  - 단어 수: {result['ocr']['word_count']}
  - 평균 신뢰도: {result['ocr']['confidence']:.2%}
  - 텍스트 길이: {len(result['ocr']['raw_text'])} 자

LLM 보정:
  - 활성화: {'예' if result['correction'] else '아니오'}
  - 성공: {'예' if result['correction'] and result['correction']['success'] else '아니오'}
  - 모델: {result['correction']['model'] if result['correction'] else 'N/A'}
  - 오류: {result['correction']['error'] if result['correction'] and result['correction']['error'] else '없음'}

보정 전후 비교:
  - 원본 길이: {len(result['ocr']['raw_text'])} 자
  - 보정 길이: {len(result['correction']['corrected_text']) if result['correction'] else 0} 자
        """
        
        self.stats_text_edit.setText(stats_text.strip())
    
    def clear_results(self):
        """결과 초기화"""
        self.raw_text_edit.clear()
        self.corrected_text_edit.clear()
        self.stats_text_edit.clear()
        self.copy_raw_button.setEnabled(False)
        self.copy_corrected_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.export_button.setEnabled(False)
    
    def copy_raw_text(self):
        """원본 텍스트 복사"""
        text = self.raw_text_edit.toPlainText()
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "복사", "원본 텍스트가 클립보드에 복사되었습니다.")
    
    def copy_corrected_text(self):
        """보정된 텍스트 복사"""
        text = self.corrected_text_edit.toPlainText()
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "복사", "보정된 텍스트가 클립보드에 복사되었습니다.")
    
    def save_result(self):
        """결과 저장"""
        if not self.current_result:
            QMessageBox.warning(self, "경고", "저장할 결과가 없습니다.")
            return
        
        try:
            base_name = Path(self.current_result['filename']).stem
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            
            # JSON 저장
            json_path = OUTPUT_DIR / f"{base_name}_{timestamp}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_result, f, ensure_ascii=False, indent=2)
            
            # 원본 텍스트 저장
            raw_path = OUTPUT_DIR / f"{base_name}_{timestamp}_raw.txt"
            with open(raw_path, 'w', encoding='utf-8') as f:
                f.write(self.current_result['ocr']['raw_text'])
            
            # 보정된 텍스트 저장
            if self.current_result['correction']:
                corrected_path = OUTPUT_DIR / f"{base_name}_{timestamp}_corrected.txt"
                with open(corrected_path, 'w', encoding='utf-8') as f:
                    f.write(self.current_result['correction']['corrected_text'])
            
            QMessageBox.information(self, "저장 완료", f"결과가 저장되었습니다:\n{OUTPUT_DIR}")
            logger.info(f"결과 저장 완료: {OUTPUT_DIR}")
        
        except Exception as e:
            logger.error(f"저장 오류: {str(e)}")
            QMessageBox.critical(self, "저장 오류", f"결과 저장 중 오류가 발생했습니다:\n{str(e)}")
    
    def export_result(self):
        """결과 내보내기 (선택한 형식)"""
        if not self.current_result:
            QMessageBox.warning(self, "경고", "내보낼 결과가 없습니다.")
            return
        
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "결과 저장",
            str(OUTPUT_DIR / self.current_result['filename']),
            "텍스트 파일 (*.txt);;JSON 파일 (*.json);;모든 파일 (*.*)"
        )
        
        if file_path:
            try:
                if selected_filter == "텍스트 파일 (*.txt)":
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(self.corrected_text_edit.toPlainText())
                elif selected_filter == "JSON 파일 (*.json)":
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(self.current_result, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(self, "내보내기 완료", f"파일이 저장되었습니다:\n{file_path}")
                logger.info(f"결과 내보내기 완료: {file_path}")
            
            except Exception as e:
                logger.error(f"내보내기 오류: {str(e)}")
                QMessageBox.critical(self, "내보내기 오류", f"내보내기 중 오류가 발생했습니다:\n{str(e)}")
    
    def update_status(self, status: ProcessStatus):
        """상태 업데이트"""
        status_colors = {
            ProcessStatus.IDLE: "#4CAF50",
            ProcessStatus.LOADING_MODELS: "#FF9800",
            ProcessStatus.PROCESSING_OCR: "#FF9800",
            ProcessStatus.PROCESSING_LLM: "#FF9800",
            ProcessStatus.COMPLETED: "#4CAF50",
            ProcessStatus.ERROR: "#F44336"
        }
        
        color = status_colors.get(status, "#666")
        self.statusbar.setStyleSheet(f"background-color: {color}; color: white; padding: 5px;")
        self.statusbar.showMessage(status.value)


def main():
    app = QApplication(sys.argv)
    window = OCRGuiApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
