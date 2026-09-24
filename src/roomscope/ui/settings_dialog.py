"""Settings dialog: language, profile, backend, output folder, copy-recording,
theme and the developer tools switch."""

from __future__ import annotations

from dataclasses import replace
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
from roomscope.interpretation.profiles import profile_title
from roomscope.settings import load_settings, save_settings


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
            self.profile.addItem(profile_title(name), name)
        profile_index = self.profile.findData(self._settings.default_profile or "generic")
        self.profile.setCurrentIndex(max(profile_index, 0))
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
        self.theme = QComboBox()
        self.theme.addItem(_("Follow the system"), "")
        self.theme.addItem(_("Light"), "light")
        self.theme.addItem(_("Dark"), "dark")
        self.theme.setCurrentIndex(max(self.theme.findData(self._settings.theme), 0))
        self.developer_tools = QCheckBox(
            _("Show developer tools (Developer menu, advanced audio options; after a restart)")
        )
        self.developer_tools.setChecked(self._settings.developer_tools)
        form.addRow(_("Language"), self.language)
        form.addRow(_("Default profile"), self.profile)
        form.addRow(_("Audio backend"), self.backend)
        form.addRow(_("Default output folder"), folder_row)
        form.addRow(self.copy_recording)
        form.addRow(_("Theme"), self.theme)
        form.addRow(self.developer_tools)
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
        # Start from the stored settings so fields this dialog does not show
        # survive a save.
        settings = replace(
            self._settings,
            language=str(self.language.currentData() or ""),
            default_profile=str(self.profile.currentData() or "generic"),
            audio_backend=str(self.backend.currentData() or ""),
            output_dir=self.output_dir.text().strip(),
            copy_recording=self.copy_recording.isChecked(),
            theme=str(self.theme.currentData() or ""),
            developer_tools=self.developer_tools.isChecked(),
        )
        save_settings(settings)
        from PySide6.QtWidgets import QApplication

        from roomscope.ui.theme import apply_application_chrome

        app = QApplication.instance()
        if app is not None:
            apply_application_chrome(app)
        if settings.language:
            activate(settings.language)
        else:
            activate(None)
        super().accept()

    def selected_output_dir(self) -> Path | None:
        text = self.output_dir.text().strip()
        return Path(text) if text else None
