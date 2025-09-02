# tabs/encoder_tab.py
"""
This module defines the EncoderTab class, which provides a user interface for configuring
the encoder settings, managing calibration, and setting up the motor's startup behavior.
"""
from PySide6.QtWidgets import (
    QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QGroupBox, QComboBox, QCheckBox, QMessageBox, QFormLayout, QWidget, QRadioButton
)
from PySide6.QtGui import QFont, QIntValidator, QDoubleValidator
# QEvent é necessário para a tradução dinâmica ---
from PySide6.QtCore import Qt, QThread, QLocale, QEvent

from .base_tab import BaseTab
from .workers import EncoderCalibrationWorker
from app_config import AppColors, AppMessages

ENCODER_MODES = {"INCREMENTAL": 0, "HALL": 1, "SIN/COS": 2, "SPI ABS AMS": 3, "SPI ABS CUI": 4, "SPI ABS TMAG5170": 5, "ABSOLUTE UART": 6, "ABSOLUTE I2C": 7}

class EncoderTab(BaseTab):
    """
    Manages the UI tab for encoder configuration and calibration.
    """
    def __init__(self, main_window, parent=None):
        """Initializes the EncoderTab, setting up UI and internal state."""
        super().__init__(main_window, parent)
        self.calib_thread = None
        self.calib_worker = None
        self._closed_loop_startup_state = False
        self._setup_ui()
        # Chama a re-tradução na inicialização ---
        self.retranslate_ui()

    # - Adiciona o método changeEvent ---
    def changeEvent(self, event):
        """Catches language change events to re-translate the UI."""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslate_ui()
        super().changeEvent(event)

    def _setup_ui(self):
        """Constructs the user interface widgets and layouts for this tab."""
        overall_layout = QVBoxLayout(self)
        columns_layout = QHBoxLayout()
        left_column_layout = QVBoxLayout()
        right_column_layout = QVBoxLayout()

        # --- Basic Settings ---
        self.basic_group = QGroupBox()
        basic_layout = QFormLayout(self.basic_group)
        self.label_encoder_mode = QLabel()
        self.encoder_mode = QComboBox()
        self.label_cpr = QLabel()
        self.encoder_cpr = QLineEdit()
        self.label_bandwidth = QLabel()
        self.encoder_bandwidth = QLineEdit()
        for name, value in ENCODER_MODES.items(): self.encoder_mode.addItem(name, value)
        basic_layout.addRow(self.label_encoder_mode, self.encoder_mode)
        basic_layout.addRow(self.label_cpr, self.encoder_cpr)
        basic_layout.addRow(self.label_bandwidth, self.encoder_bandwidth)
        calibration_layout = QHBoxLayout()
        self.label_calib_status = QLabel()
        self.calibration_status_indicator = QLabel()
        self.calibration_status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.calibration_status_indicator.setMinimumWidth(110)
        self.calibrate_encoder_button = QPushButton()
        calibration_layout.addWidget(self.calibration_status_indicator)
        calibration_layout.addStretch()
        calibration_layout.addWidget(self.calibrate_encoder_button)
        basic_layout.addRow(self.label_calib_status, calibration_layout)
        left_column_layout.addWidget(self.basic_group)
        left_column_layout.addStretch()
        
        # --- Startup Method ---
        self.startup_method_group = QGroupBox()
        startup_method_layout = QVBoxLayout(self.startup_method_group)
        self.radio_none = QRadioButton()
        self.radio_calibrate_on_startup = QRadioButton()
        self.radio_use_index = QRadioButton()
        self.index_options_group = QGroupBox()
        self.index_options_group.setFlat(True)
        index_options_layout = QVBoxLayout(self.index_options_group)
        self.save_calibration_check = QCheckBox()
        self.startup_index_search_check = QCheckBox()
        index_options_layout.addWidget(self.save_calibration_check)
        index_options_layout.addWidget(self.startup_index_search_check)
        index_options_layout.setContentsMargins(20, 5, 5, 5)
        startup_method_layout.addWidget(self.radio_none)
        startup_method_layout.addWidget(self.radio_calibrate_on_startup)
        startup_method_layout.addWidget(self.radio_use_index)
        startup_method_layout.addWidget(self.index_options_group)
        self.radio_none.setChecked(True)

        # --- Closed-Loop Control ---
        self.closed_loop_group = QGroupBox()
        closed_loop_layout = QHBoxLayout(self.closed_loop_group)
        self.closed_loop_status_indicator = QLabel()
        self.closed_loop_status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.closed_loop_status_indicator.setMinimumWidth(110)
        self.toggle_closed_loop_button = QPushButton("...")
        closed_loop_layout.addWidget(self.closed_loop_status_indicator)
        closed_loop_layout.addStretch()
        closed_loop_layout.addWidget(self.toggle_closed_loop_button)
        right_column_layout.addWidget(self.startup_method_group)
        right_column_layout.addWidget(self.closed_loop_group)
        right_column_layout.addStretch()

        # --- Layout Assembly ---
        columns_layout.addLayout(left_column_layout)
        columns_layout.addLayout(right_column_layout)
        self.apply_btn = QPushButton()
        self.apply_btn.clicked.connect(self.apply_config)
        overall_layout.addLayout(columns_layout)
        overall_layout.addStretch() 
        overall_layout.addWidget(self.apply_btn, 0, Qt.AlignmentFlag.AlignRight)
        
        # --- Input Validators ---
        c_locale = QLocale(QLocale.Language.C)
        cpr_validator = QIntValidator(1, 9999999, self); self.encoder_cpr.setValidator(cpr_validator)
        bandwidth_validator = QDoubleValidator(0.0, 10000.0, 2, self)
        bandwidth_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        bandwidth_validator.setLocale(c_locale); self.encoder_bandwidth.setValidator(bandwidth_validator)

        # --- Signal Connections ---
        self.calibrate_encoder_button.clicked.connect(self.start_full_calibration)
        self.toggle_closed_loop_button.clicked.connect(self.on_toggle_closed_loop)
        self.radio_none.toggled.connect(self._update_startup_mode_ui)
        self.radio_calibrate_on_startup.toggled.connect(self._update_startup_mode_ui)
        self.radio_use_index.toggled.connect(self._update_startup_mode_ui)
        self.startup_index_search_check.toggled.connect(self._update_closed_loop_dependency)
        self.radio_calibrate_on_startup.toggled.connect(self._update_closed_loop_dependency)

    # --- MUDANÇA: Adiciona a nova função retranslate_ui ---
    def retranslate_ui(self):
        """Updates all translatable texts in this tab."""
        self.basic_group.setTitle(self.tr("Basic Encoder Settings (Axis 0)"))
        self.label_encoder_mode.setText(self.tr("Encoder Mode:"))
        self.label_cpr.setText(self.tr("CPR (Counts Per Revolution):"))
        self.label_bandwidth.setText(self.tr("Bandwidth (Hz):"))
        self.label_calib_status.setText(self.tr("Calibration Status:"))
        self.startup_method_group.setTitle(self.tr("Startup Method"))
        self.radio_none.setText(self.tr("No Action on Startup (Default)"))
        self.radio_calibrate_on_startup.setText(self.tr("Encoder without Index (Calibrate on Each Startup)"))
        self.radio_use_index.setText(self.tr("Use Z-Index (Fast Startup)"))
        self.save_calibration_check.setText(self.tr("Save Calibration (pre_calibrated)"))
        self.startup_index_search_check.setText(self.tr("Search for Index on Startup"))
        self.closed_loop_group.setTitle(self.tr("Closed-Loop Control on Startup"))
        self.apply_btn.setText(self.tr("Apply Settings"))
        
        # Update dynamic labels
        self.calibration_status_indicator.setText(self.tr("UNKNOWN"))
        self.closed_loop_status_indicator.setText(self.tr("UNKNOWN"))
        self._update_startup_mode_ui()

    def _update_startup_mode_ui(self):
        """Updates UI elements based on the selected startup radio button."""
        is_index_mode = self.radio_use_index.isChecked()
        self.index_options_group.setEnabled(is_index_mode)
        button_text = self.tr("Calibrate with Index") if is_index_mode else self.tr("Calibrate Encoder")
        self.calibrate_encoder_button.setText(button_text)
        self._update_closed_loop_dependency()
        
    def _update_closed_loop_dependency(self):
        """Automatically enables/disables closed-loop on startup based on other settings."""
        is_cal_on_startup = self.radio_calibrate_on_startup.isChecked()
        is_index_search_on = self.radio_use_index.isChecked() and self.startup_index_search_check.isChecked()
        if is_cal_on_startup or is_index_search_on:
            self._closed_loop_startup_state = True; self.toggle_closed_loop_button.setEnabled(False)
        else:
            self._closed_loop_startup_state = False; self.toggle_closed_loop_button.setEnabled(True)
        self.update_closed_loop_ui()
        
    def start_full_calibration(self):
        """Initiates the encoder calibration sequence in a background thread."""
        odrv = self.get_odrv()
        if not odrv: return
        self.calibrate_encoder_button.setEnabled(False)
        self.calib_thread = QThread()
        self.calib_worker = EncoderCalibrationWorker(odrv, self.radio_use_index.isChecked())
        self.calib_worker.moveToThread(self.calib_thread)
        self.calib_thread.started.connect(self.calib_worker.run)
        self.calib_worker.finished.connect(self.calib_thread.quit)
        self.calib_worker.finished.connect(self.calib_worker.deleteLater)
        self.calib_thread.finished.connect(self.calib_thread.deleteLater)
        self.calib_worker.progress.connect(self.calibrate_encoder_button.setText)
        self.calib_worker.result.connect(self.on_calibration_result)
        self.calib_thread.start()
        
    def on_calibration_result(self, success, message):
        """Handles the result of the encoder calibration worker."""
        self._update_startup_mode_ui()
        self.calibrate_encoder_button.setEnabled(True)
        if success:
            final_message = message
            if self.radio_use_index.isChecked():
                final_message += self.tr("\n\nTo use this calibration on startup, check 'Save Calibration' and 'Search for Index on Startup', apply, and save.")
            QMessageBox.information(self, self.tr(AppMessages.CALIBRATION_SUCCESS), final_message)
        else:
            QMessageBox.critical(self, self.tr(AppMessages.CALIBRATION_FAILED), message)
        self.main_window.populate_all_fields()
        
    def update_calibration_status(self, is_ready):
        """Updates the visual status indicator for encoder calibration."""
        if is_ready:
            self.calibration_status_indicator.setText(self.tr("CALIBRATED"))
            style = f"background-color: {AppColors.STATUS_CALIBRATED_BG}; color: {AppColors.STATUS_TEXT}; border-radius: 0px; padding: 2px 4px; font-weight: bold;"
        else:
            self.calibration_status_indicator.setText(self.tr("NOT CALIBRATED"))
            style = f"background-color: {AppColors.STATUS_NOT_CALIBRATED_BG}; color: {AppColors.STATUS_TEXT}; border-radius: 0px; padding: 2px 4px; font-weight: bold;"
        self.calibration_status_indicator.setStyleSheet(style)
            
    def update_closed_loop_ui(self):
        """Updates the visual status indicator for the 'Closed-Loop on Startup' feature."""
        if self._closed_loop_startup_state:
            self.closed_loop_status_indicator.setText(self.tr("ENABLED"))
            style = f"background-color: {AppColors.STATUS_CALIBRATED_BG}; color: {AppColors.STATUS_TEXT}; border-radius: 0px; padding: 2px 4px; font-weight: bold;"
            self.toggle_closed_loop_button.setText(self.tr("Disable"))
        else:
            self.closed_loop_status_indicator.setText(self.tr("DISABLED"))
            style = f"background-color: {AppColors.STATUS_NOT_CALIBRATED_BG}; color: {AppColors.STATUS_TEXT}; border-radius: 0px; padding: 2px 4px; font-weight: bold;"
            self.toggle_closed_loop_button.setText(self.tr("Enable"))
        self.closed_loop_status_indicator.setStyleSheet(style)
            
    def on_toggle_closed_loop(self):
        """Toggles the internal state for closed-loop on startup."""
        self._closed_loop_startup_state = not self._closed_loop_startup_state
        self.update_closed_loop_ui()
        
    def populate_fields(self):
        """Reads encoder configuration from the connected ODrive and updates the UI fields."""
        odrv = self.get_odrv()
        if not odrv: return
        mode_data = odrv.axis0.encoder.config.mode
        mode_index = self.encoder_mode.findData(mode_data)
        self.encoder_mode.setCurrentIndex(mode_index if mode_index != -1 else 0)
        self.encoder_cpr.setText(str(odrv.axis0.encoder.config.cpr))
        self.encoder_bandwidth.setText(f"{odrv.axis0.encoder.config.bandwidth:.2f}")
        
        if odrv.axis0.config.startup_encoder_offset_calibration: self.radio_calibrate_on_startup.setChecked(True)
        elif odrv.axis0.encoder.config.use_index: self.radio_use_index.setChecked(True)
        else: self.radio_none.setChecked(True)
        
        self.save_calibration_check.setChecked(odrv.axis0.encoder.config.pre_calibrated)
        self.startup_index_search_check.setChecked(odrv.axis0.config.startup_encoder_index_search)
        self._closed_loop_startup_state = odrv.axis0.config.startup_closed_loop_control
        self.update_calibration_status(odrv.axis0.encoder.is_ready)
        self._update_startup_mode_ui()
        
    def apply_config(self):
        """Applies the settings from the UI fields to the connected ODrive."""
        odrv = self.get_odrv()
        if not odrv: return
        try:
            odrv.axis0.encoder.config.mode = self.encoder_mode.currentData()
            odrv.axis0.encoder.config.cpr = int(self.encoder_cpr.text())
            odrv.axis0.encoder.config.bandwidth = float(self.encoder_bandwidth.text().replace(',', '.'))
            
            if self.radio_calibrate_on_startup.isChecked():
                odrv.axis0.config.startup_encoder_offset_calibration = True; odrv.axis0.encoder.config.use_index = False; odrv.axis0.encoder.config.pre_calibrated = False; odrv.axis0.config.startup_encoder_index_search = False
            elif self.radio_use_index.isChecked():
                odrv.axis0.config.startup_encoder_offset_calibration = False; odrv.axis0.encoder.config.use_index = True; odrv.axis0.encoder.config.pre_calibrated = self.save_calibration_check.isChecked(); odrv.axis0.config.startup_encoder_index_search = self.startup_index_search_check.isChecked()
            else:
                odrv.axis0.config.startup_encoder_offset_calibration = False; odrv.axis0.encoder.config.use_index = False; odrv.axis0.encoder.config.pre_calibrated = False; odrv.axis0.config.startup_encoder_index_search = False
            
            odrv.axis0.config.startup_closed_loop_control = self._closed_loop_startup_state
            
            self.main_window.show_status_message(self.tr(AppMessages.CONFIG_APPLY_SUCCESS), AppColors.SUCCESS, 3000)
            reminder_msg = f"{self.tr(AppMessages.CONFIG_APPLY_SUCCESS)}.\n\n{self.tr(AppMessages.SAVE_REMINDER)}"
            QMessageBox.information(self, self.tr("Important Reminder"), reminder_msg)
        except (ValueError, TypeError):
            QMessageBox.critical(self, self.tr("Input Error"), self.tr("Please enter valid, non-empty numerical values."))
        except Exception as e:
            error_msg = self.tr(AppMessages.CONFIG_APPLY_ERROR).format(e)
            self.main_window.show_status_message(error_msg, AppColors.ERROR, 5000)