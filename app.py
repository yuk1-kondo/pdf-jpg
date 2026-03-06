import os
import sys
from dataclasses import dataclass

import pypdfium2 as pdfium
from PIL import Image
from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSlider,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


@dataclass
class ConvertConfig:
    output_dir: str
    dpi: int
    quality: int


class DropArea(QLabel):
    files_dropped = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(220)
        self.setText(
            "Drop PDF files here\n"
            "or click the button below\n\n"
            "(Multiple files supported)"
        )
        self.setObjectName("dropArea")

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("dragActive", True)
            self.style().unpolish(self)
            self.style().polish(self)
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)

        urls = event.mimeData().urls()
        pdf_files = []
        for url in urls:
            local_path = url.toLocalFile()
            if local_path.lower().endswith(".pdf") and os.path.isfile(local_path):
                pdf_files.append(local_path)

        if pdf_files:
            self.files_dropped.emit(pdf_files)


class ConvertWorker(QThread):
    progress = Signal(int)
    log = Signal(str)
    completed = Signal()
    failed = Signal(str)

    def __init__(self, pdf_files: list[str], config: ConvertConfig) -> None:
        super().__init__()
        self.pdf_files = pdf_files
        self.config = config

    def run(self) -> None:
        try:
            all_pages = 0
            for pdf_path in self.pdf_files:
                doc = pdfium.PdfDocument(pdf_path)
                all_pages += len(doc)
                doc.close()

            if all_pages == 0:
                self.failed.emit("No pages found in PDF files.")
                return

            processed = 0
            scale = self.config.dpi / 72.0

            for pdf_path in self.pdf_files:
                base_name = os.path.splitext(os.path.basename(pdf_path))[0]
                doc = pdfium.PdfDocument(pdf_path)

                for page_index in range(len(doc)):
                    page = doc[page_index]
                    bitmap = page.render(scale=scale)
                    pil_image = bitmap.to_pil().convert("RGB")

                    output_name = f"{base_name}_page_{page_index + 1:03d}.jpg"
                    output_path = os.path.join(self.config.output_dir, output_name)

                    pil_image.save(
                        output_path,
                        format="JPEG",
                        quality=self.config.quality,
                        optimize=True,
                    )

                    processed += 1
                    percentage = int((processed / all_pages) * 100)
                    self.progress.emit(percentage)
                    self.log.emit(f"Saved: {output_path}")

                doc.close()

            self.completed.emit()
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("NeonPDF Shot - PDF to JPG")
        self.resize(920, 680)

        self.pdf_files: list[str] = []
        self.worker: ConvertWorker | None = None

        self._build_ui()
        self._apply_style()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(14)

        title = QLabel("PDF to JPG Converter")
        title.setObjectName("title")
        subtitle = QLabel(
            "Local-only conversion for Windows. Fast drag & drop workflow."
        )
        subtitle.setObjectName("subtitle")

        self.drop_area = DropArea()
        self.drop_area.files_dropped.connect(self._on_files_selected)

        controls = QWidget()
        grid = QGridLayout(controls)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        output_label = QLabel("Output folder")
        self.output_path_label = QLabel(os.path.expanduser("~/Desktop"))
        self.output_path_label.setObjectName("outputPath")
        self.choose_output_btn = QPushButton("Choose")
        self.choose_output_btn.clicked.connect(self._choose_output_dir)

        dpi_label = QLabel("DPI")
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 600)
        self.dpi_spin.setValue(200)

        quality_label = QLabel("JPG Quality")
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(40, 100)
        self.quality_slider.setValue(90)
        self.quality_value = QLabel("90")
        self.quality_slider.valueChanged.connect(
            lambda val: self.quality_value.setText(str(val))
        )

        grid.addWidget(output_label, 0, 0)
        grid.addWidget(self.output_path_label, 0, 1)
        grid.addWidget(self.choose_output_btn, 0, 2)
        grid.addWidget(dpi_label, 1, 0)
        grid.addWidget(self.dpi_spin, 1, 1)
        grid.addWidget(quality_label, 2, 0)
        grid.addWidget(self.quality_slider, 2, 1)
        grid.addWidget(self.quality_value, 2, 2)

        btn_row = QHBoxLayout()
        self.select_btn = QPushButton("Select PDF files")
        self.select_btn.clicked.connect(self._pick_files)
        self.convert_btn = QPushButton("Convert to JPG")
        self.convert_btn.clicked.connect(self._convert)
        self.convert_btn.setEnabled(False)

        btn_row.addWidget(self.select_btn)
        btn_row.addWidget(self.convert_btn)

        self.progress = QProgressBar()
        self.progress.setValue(0)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(180)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.drop_area)
        layout.addWidget(controls)
        layout.addLayout(btn_row)
        layout.addWidget(self.progress)
        layout.addWidget(self.log)

    def _apply_style(self) -> None:
        font = QFont("Segoe UI Variable")
        QApplication.instance().setFont(font)

        self.setStyleSheet(
            """
            QWidget {
                color: #e9f2ff;
                background-color: #08142a;
                font-size: 14px;
            }
            QMainWindow {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #061225, stop: 0.5 #12284a, stop: 1 #0d1730
                );
            }
            QLabel#title {
                font-size: 30px;
                font-weight: 700;
                color: #ffffff;
                letter-spacing: 0.6px;
            }
            QLabel#subtitle {
                color: #9fc3ff;
                margin-bottom: 4px;
            }
            QLabel#dropArea {
                border: 2px dashed #58a6ff;
                border-radius: 16px;
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 rgba(31, 80, 160, 90), stop: 1 rgba(10, 23, 45, 140)
                );
                color: #d8e9ff;
                font-size: 20px;
                font-weight: 600;
            }
            QLabel#dropArea[dragActive=\"true\"] {
                border: 2px solid #76ffde;
                background: rgba(5, 77, 102, 150);
                color: #e6fff8;
            }
            QLabel#outputPath {
                color: #bee0ff;
                background: rgba(8, 25, 52, 130);
                border: 1px solid rgba(120, 165, 230, 100);
                border-radius: 8px;
                padding: 6px 8px;
            }
            QPushButton {
                background-color: #1f6feb;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 10px 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #3e8bff;
            }
            QPushButton:disabled {
                background-color: #3d4d6b;
                color: #9eafcd;
            }
            QSpinBox, QTextEdit {
                background: rgba(4, 20, 43, 170);
                border: 1px solid rgba(114, 157, 230, 120);
                border-radius: 8px;
                color: #e8f4ff;
                padding: 6px;
            }
            QProgressBar {
                border: 1px solid rgba(117, 161, 240, 120);
                border-radius: 8px;
                text-align: center;
                background: rgba(6, 24, 52, 160);
                color: #ecf6ff;
                min-height: 20px;
            }
            QProgressBar::chunk {
                border-radius: 8px;
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #00c1a2, stop: 1 #39b8ff
                );
            }
            """
        )

    def _pick_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select PDF files",
            "",
            "PDF files (*.pdf)",
        )
        if files:
            self._on_files_selected(files)

    def _on_files_selected(self, files: list[str]) -> None:
        self.pdf_files = files
        self.convert_btn.setEnabled(True)
        self.log.append(f"Loaded {len(files)} PDF file(s).")
        self.drop_area.setText(
            f"{len(files)} PDF file(s) ready.\nClick Convert to JPG to start."
        )

    def _choose_output_dir(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Choose output folder",
            self.output_path_label.text(),
        )
        if selected:
            self.output_path_label.setText(selected)

    def _convert(self) -> None:
        if not self.pdf_files:
            QMessageBox.warning(
                self, "No PDF", "Please drop or select at least one PDF file."
            )
            return

        output_dir = self.output_path_label.text().strip()
        if not os.path.isdir(output_dir):
            QMessageBox.warning(
                self, "Invalid output", "Please choose a valid output folder."
            )
            return

        self.progress.setValue(0)
        self.log.append("--- Conversion started ---")
        self.convert_btn.setEnabled(False)
        self.select_btn.setEnabled(False)

        cfg = ConvertConfig(
            output_dir=output_dir,
            dpi=self.dpi_spin.value(),
            quality=self.quality_slider.value(),
        )

        self.worker = ConvertWorker(self.pdf_files, cfg)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.log.connect(self.log.append)
        self.worker.completed.connect(self._on_completed)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_completed(self) -> None:
        self.log.append("--- Conversion completed ---")
        self.convert_btn.setEnabled(True)
        self.select_btn.setEnabled(True)
        QMessageBox.information(self, "Done", "PDF to JPG conversion completed.")

    def _on_failed(self, message: str) -> None:
        self.log.append(f"Error: {message}")
        self.convert_btn.setEnabled(True)
        self.select_btn.setEnabled(True)
        QMessageBox.critical(self, "Conversion failed", message)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
