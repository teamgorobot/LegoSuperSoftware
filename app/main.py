import json
import traceback
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QClipboard
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app_settings import AppSettings, load_settings, save_settings
from ai_openai import generate_with_openai
from ai_local import generate_with_local
from ai_local_multi import generate_with_local_multi


class GenerateThread(QThread):
    success = Signal(dict)
    failed = Signal(str)

    def __init__(self, settings: AppSettings, payload: dict, image_paths: list[str]):
        super().__init__()
        self.settings = settings
        self.payload = payload
        self.image_paths = image_paths

    def run(self):
        try:
            mode = self.settings.ai_mode
            if mode == "local":
                raw = generate_with_local(self.settings, self.payload)
            elif mode == "local_multi":
                raw = generate_with_local_multi(self.settings, self.payload, self.image_paths)
            elif mode == "openai":
                raw = generate_with_openai(self.settings, self.payload, self.image_paths)
            else:
                raw = self._auto_generate()

            data = parse_model_output(raw)
            self.success.emit(data)
        except Exception as exc:
            self.failed.emit(f"{exc}\n\n{traceback.format_exc()}")

    def _auto_generate(self):
        if self.settings.local_code_model_path and self.settings.local_tutorial_model_path:
            try:
                return generate_with_local_multi(self.settings, self.payload, self.image_paths)
            except Exception:
                pass

        if self.settings.local_model_path:
            try:
                return generate_with_local(self.settings, self.payload)
            except Exception:
                pass
        return generate_with_openai(self.settings, self.payload, self.image_paths)


def parse_model_output(text: str) -> dict:
    if not text:
        return {"code": "", "tutorial": ""}

    cleaned = text.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start : end + 1])
        except Exception:
            pass

    return {
        "code": cleaned,
        "tutorial": "",
    }


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LegoSuperSoftware")
        self.resize(1200, 760)

        self.settings = load_settings()

        self.image_paths: list[str] = []
        self.worker: GenerateThread | None = None

        self._build_ui()
        self._load_settings_into_ui()

    def _build_ui(self):
        root = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)

        input_group = QGroupBox("Inputs")
        input_layout = QFormLayout(input_group)

        self.competition_combo = QComboBox()
        self.competition_combo.addItems(["WRO", "FIRST LEGO League"])
        input_layout.addRow("Competition", self.competition_combo)

        self.task_title = QLineEdit()
        input_layout.addRow("Task title", self.task_title)

        self.tasks_text = QPlainTextEdit()
        self.tasks_text.setPlaceholderText("Describe missions, scoring, and objectives")
        input_layout.addRow("Tasks/Missions", self.tasks_text)

        self.notes_text = QPlainTextEdit()
        self.notes_text.setPlaceholderText("Notes from the table, pictures, observations")
        input_layout.addRow("Notes", self.notes_text)

        self.parts_text = QPlainTextEdit()
        self.parts_text.setPlaceholderText("List available parts and special hardware")
        input_layout.addRow("Available parts", self.parts_text)

        self.sensors_text = QPlainTextEdit()
        self.sensors_text.setPlaceholderText("Motors, sensors, ports if known")
        input_layout.addRow("Sensors/Ports", self.sensors_text)

        self.constraints_text = QPlainTextEdit()
        self.constraints_text.setPlaceholderText("Rules or limits to respect")
        input_layout.addRow("Constraints", self.constraints_text)

        self.image_list = QListWidget()
        self.image_list.setMinimumHeight(120)
        input_layout.addRow("Photos", self.image_list)

        image_buttons = QWidget()
        image_btn_layout = QHBoxLayout(image_buttons)
        self.add_images_btn = QPushButton("Add Photos")
        self.clear_images_btn = QPushButton("Clear Photos")
        image_btn_layout.addWidget(self.add_images_btn)
        image_btn_layout.addWidget(self.clear_images_btn)
        input_layout.addRow("", image_buttons)

        left_layout.addWidget(input_group)

        settings_group = QGroupBox("AI Settings")
        settings_layout = QFormLayout(settings_group)

        self.ai_mode_combo = QComboBox()
        self.ai_mode_combo.addItems(["auto", "openai", "local", "local_multi"])
        settings_layout.addRow("AI mode", self.ai_mode_combo)

        self.openai_model_input = QLineEdit()
        settings_layout.addRow("OpenAI model", self.openai_model_input)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        settings_layout.addRow("OpenAI API key", self.api_key_input)

        self.remember_key = QCheckBox("Remember API key on this PC")
        settings_layout.addRow("", self.remember_key)

        self.include_images_check = QCheckBox("Include images in OpenAI request")
        settings_layout.addRow("", self.include_images_check)

        self.image_detail_combo = QComboBox()
        self.image_detail_combo.addItems(["auto", "low", "high"])
        settings_layout.addRow("Image detail", self.image_detail_combo)

        self.local_model_input = QLineEdit()
        settings_layout.addRow("Local model path", self.local_model_input)

        self.browse_local_model = QPushButton("Browse model")
        settings_layout.addRow("", self.browse_local_model)

        self.local_code_model_input = QLineEdit()
        settings_layout.addRow("Local code model", self.local_code_model_input)

        self.browse_local_code_model = QPushButton("Browse code model")
        settings_layout.addRow("", self.browse_local_code_model)

        self.local_tutorial_model_input = QLineEdit()
        settings_layout.addRow("Local tutorial model", self.local_tutorial_model_input)

        self.browse_local_tutorial_model = QPushButton("Browse tutorial model")
        settings_layout.addRow("", self.browse_local_tutorial_model)

        self.local_image_model_input = QLineEdit()
        settings_layout.addRow("Local image model", self.local_image_model_input)

        self.browse_local_image_model = QPushButton("Browse image model")
        settings_layout.addRow("", self.browse_local_image_model)

        left_layout.addWidget(settings_group)
        left_layout.addStretch(1)

        right = QWidget()
        right_layout = QVBoxLayout(right)

        self.tabs = QTabWidget()

        self.code_text = QPlainTextEdit()
        self.tutorial_text = QPlainTextEdit()
        self.code_text.setPlaceholderText("Pybricks code will appear here")
        self.tutorial_text.setPlaceholderText("Build tutorial will appear here")

        code_tab = QWidget()
        code_layout = QVBoxLayout(code_tab)
        self.copy_code_btn = QPushButton("Copy code")
        code_layout.addWidget(self.copy_code_btn)
        code_layout.addWidget(self.code_text)

        tutorial_tab = QWidget()
        tutorial_layout = QVBoxLayout(tutorial_tab)
        self.copy_tutorial_btn = QPushButton("Copy tutorial")
        tutorial_layout.addWidget(self.copy_tutorial_btn)
        tutorial_layout.addWidget(self.tutorial_text)

        self.tabs.addTab(code_tab, "Pybricks Code")
        self.tabs.addTab(tutorial_tab, "Build Tutorial")

        right_layout.addWidget(self.tabs)

        action_bar = QWidget()
        action_layout = QHBoxLayout(action_bar)
        self.generate_btn = QPushButton("Generate")
        self.status_label = QLabel("Ready")
        action_layout.addWidget(self.generate_btn)
        action_layout.addWidget(self.status_label)
        action_layout.addStretch(1)
        right_layout.addWidget(action_bar)

        root.addWidget(left)
        root.addWidget(right)
        root.setStretchFactor(0, 2)
        root.setStretchFactor(1, 3)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.addWidget(root)
        self.setCentralWidget(container)

        self._connect_signals()

    def _connect_signals(self):
        self.add_images_btn.clicked.connect(self._add_images)
        self.clear_images_btn.clicked.connect(self._clear_images)
        self.browse_local_model.clicked.connect(self._browse_local_model)
        self.browse_local_code_model.clicked.connect(self._browse_local_code_model)
        self.browse_local_tutorial_model.clicked.connect(self._browse_local_tutorial_model)
        self.browse_local_image_model.clicked.connect(self._browse_local_image_model)
        self.generate_btn.clicked.connect(self._generate)
        self.copy_code_btn.clicked.connect(lambda: self._copy_text(self.code_text.toPlainText()))
        self.copy_tutorial_btn.clicked.connect(lambda: self._copy_text(self.tutorial_text.toPlainText()))

        self.ai_mode_combo.currentTextChanged.connect(self._save_settings_from_ui)
        self.openai_model_input.textChanged.connect(self._save_settings_from_ui)
        self.api_key_input.textChanged.connect(self._save_settings_from_ui)
        self.remember_key.stateChanged.connect(self._save_settings_from_ui)
        self.include_images_check.stateChanged.connect(self._save_settings_from_ui)
        self.image_detail_combo.currentTextChanged.connect(self._save_settings_from_ui)
        self.local_model_input.textChanged.connect(self._save_settings_from_ui)
        self.local_code_model_input.textChanged.connect(self._save_settings_from_ui)
        self.local_tutorial_model_input.textChanged.connect(self._save_settings_from_ui)
        self.local_image_model_input.textChanged.connect(self._save_settings_from_ui)
        self.competition_combo.currentTextChanged.connect(self._save_settings_from_ui)

    def _load_settings_into_ui(self):
        self.competition_combo.setCurrentText(self.settings.competition)
        self.ai_mode_combo.setCurrentText(self.settings.ai_mode)
        self.openai_model_input.setText(self.settings.openai_model)
        self.api_key_input.setText(self.settings.openai_api_key)
        self.remember_key.setChecked(self.settings.remember_api_key)
        self.include_images_check.setChecked(self.settings.include_images)
        self.image_detail_combo.setCurrentText(self.settings.image_detail)
        self.local_model_input.setText(self.settings.local_model_path)
        self.local_code_model_input.setText(self.settings.local_code_model_path)
        self.local_tutorial_model_input.setText(self.settings.local_tutorial_model_path)
        self.local_image_model_input.setText(self.settings.local_image_model_path)

    def _save_settings_from_ui(self):
        self.settings.competition = self.competition_combo.currentText()
        self.settings.ai_mode = self.ai_mode_combo.currentText()
        self.settings.openai_model = self.openai_model_input.text().strip() or "gpt-5"
        self.settings.openai_api_key = self.api_key_input.text().strip()
        self.settings.remember_api_key = self.remember_key.isChecked()
        self.settings.include_images = self.include_images_check.isChecked()
        self.settings.image_detail = self.image_detail_combo.currentText()
        self.settings.local_model_path = self.local_model_input.text().strip()
        self.settings.local_code_model_path = self.local_code_model_input.text().strip()
        self.settings.local_tutorial_model_path = self.local_tutorial_model_input.text().strip()
        self.settings.local_image_model_path = self.local_image_model_input.text().strip()

        save_settings(self.settings)

    def _add_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select photos",
            str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if not files:
            return

        for path in files:
            if path not in self.image_paths:
                self.image_paths.append(path)
                item = QListWidgetItem(Path(path).name)
                item.setToolTip(path)
                self.image_list.addItem(item)

    def _clear_images(self):
        self.image_paths = []
        self.image_list.clear()

    def _browse_local_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select local .gguf model",
            str(Path.home()),
            "GGUF Models (*.gguf)"
        )
        if path:
            self.local_model_input.setText(path)

    def _browse_local_code_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select local code .gguf model",
            str(Path.home()),
            "GGUF Models (*.gguf)"
        )
        if path:
            self.local_code_model_input.setText(path)

    def _browse_local_tutorial_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select local tutorial .gguf model",
            str(Path.home()),
            "GGUF Models (*.gguf)"
        )
        if path:
            self.local_tutorial_model_input.setText(path)

    def _browse_local_image_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select local image .gguf model",
            str(Path.home()),
            "GGUF Models (*.gguf)"
        )
        if path:
            self.local_image_model_input.setText(path)

    def _generate(self):
        if self.worker and self.worker.isRunning():
            return

        self._save_settings_from_ui()

        payload = {
            "competition": self.competition_combo.currentText(),
            "task_title": self.task_title.text().strip(),
            "tasks": self.tasks_text.toPlainText(),
            "notes": self.notes_text.toPlainText(),
            "parts": self.parts_text.toPlainText(),
            "sensors": self.sensors_text.toPlainText(),
            "constraints": self.constraints_text.toPlainText(),
        }

        self.status_label.setText("Generating...")
        self.generate_btn.setEnabled(False)

        self.worker = GenerateThread(self.settings, payload, self.image_paths)
        self.worker.success.connect(self._on_success)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_success(self, data: dict):
        self.code_text.setPlainText(data.get("code", ""))
        self.tutorial_text.setPlainText(data.get("tutorial", ""))
        self.status_label.setText("Done")
        self.generate_btn.setEnabled(True)

    def _on_failed(self, error: str):
        self.status_label.setText("Error")
        self.generate_btn.setEnabled(True)
        QMessageBox.critical(self, "Generation failed", error)

    def _copy_text(self, text: str):
        if not text:
            return
        QApplication.clipboard().setText(text, QClipboard.Clipboard)
        self.status_label.setText("Copied to clipboard")


def main():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
