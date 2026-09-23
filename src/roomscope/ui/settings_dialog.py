"""Settings dialog: language, profile, backend, output folder, copy-recording."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from roomscope.i18n import _, activate, available_locales
from roomscope.interpretation import available_profiles
from roomscope.settings import UserSettings, load_settings, save_settings


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(_("Settings"))
        self._settings = load_settings()
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.language = QComboBox()
        self.language.addItem(_("System / English fallback"), "")
        for tag in available_locales():
            self.language.addItem(tag, tag)
        index = self.language.findData(self._settings.language)
        self.language.setCurrentIndex(max(index, 0))
        self.profile = QComboBox()
        for name in available_profiles():
            self.profile.addItem(name)
        self.profile.setCurrentText(self._settings.default_profile or "generic")
        self.backend = QComboBox()
        self.backend.addItem(_("Default (PortAudio)"), "")
        self.backend.addItem("portaudio", "portaudio")
        self.backend.addItem("fake", "fake")
        backend_index = self.backend.findData(self._settings.audio_backend)
        self.backend.setCurrentIndex(max(backend_index, 0))
        folder_row = QHBoxLayout()
        self.output_dir = QLineEdit(self._settings.output_dir)
        browse = QPushButton(_("Browse..."))
        browse.clicked.connect(self._browse)
        folder_row.addWidget(self.output_dir)
        folder_row.addWidget(browse)
        self.copy_recording = QCheckBox(_("Copy the raw recording into every session"))
        self.copy_recording.setChecked(self._settings.copy_recording)
        form.addRow(_("Language"), self.language)
        form.addRow(_("Default profile"), self.profile)
        form.addRow(_("Audio backend"), self.backend)
        form.addRow(_("Default output folder"), folder_row)
        form.addRow(self.copy_recording)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, _("Default output folder"))
        if directory:
            self.output_dir.setText(directory)

    def accept(self) -> None:
        settings = UserSettings(
            language=str(self.language.currentData() or ""),
            default_profile=self.profile.currentText() or "generic",
            audio_backend=str(self.backend.currentData() or ""),
            output_dir=self.output_dir.text().strip(),
            copy_recording=self.copy_recording.isChecked(),
        )
        save_settings(settings)
        if settings.language:
            activate(settings.language)
        else:
            activate(None)
        super().accept()

    def selected_output_dir(self) -> Path | None:
        text = self.output_dir.text().strip()
        return Path(text) if text else None
