# tabs/motor_tab.py
"""
This module defines the MotorTab class, which provides a user interface for configuring
and calibrating the motor connected to an ODrive controller (Axis 0).
"""
from PySide6.QtWidgets import (
    QLabel, QLineEdit, QPushButton, QVBoxLayout, QGridLayout, QGroupBox,
    QCheckBox, QComboBox, QHBoxLayout, QMessageBox, QFormLayout
)
from PySide6.QtGui import QIntValidator, QDoubleValidator
# --- MUDANÇA: QEvent é necessário para a tradução dinâmica ---
from PySide6.QtCore import Qt, QThread, QLocale, QEvent

from .base_tab import BaseTab
from .workers import MotorCalibrationWorker
from app_config import AppColors, AppMessages

from odrive.enums import (
    CONTROL_MODE_VOLTAGE_CONTROL,
    CONTROL_MODE_TORQUE_CONTROL,
    CONTROL_MODE_VELOCITY_CONTROL,
    CONTROL_MODE_POSITION_CONTROL
)

# --- Constants ---
MOTOR_TYPES = {"HIGH_CURRENT": 0, "GIMBAL": 2, "AC_INDUCTION": 1}
CONTROL_MODES = {
    "TORQUE": CONTROL_MODE_TORQUE_CONTROL,
    "VELOCITY": CONTROL_MODE_VELOCITY_CONTROL,
    "POSITION": CONTROL_MODE_POSITION_CONTROL,
    "VOLTAGE": CONTROL_MODE_VOLTAGE_CONTROL
}

class MotorTab(BaseTab):
    """
    Manages the UI tab for motor configuration, including main parameters,
    limits, and the calibration process.
    """
    def __init__(self, main_window, parent=None):
        """Initializes the MotorTab, setting up UI and internal state."""
        super().__init__(main_window, parent)
        self.calib_thread = None
        self.calib_worker = None
        self._setup_ui()
        # --- MUDANÇA: Chama a re-tradução na inicialização ---
        self.retranslate_ui()

    # --- MUDANÇA: Adiciona o método changeEvent ---
    def changeEvent(self, event):
        """Catches language change events to re-translate the UI."""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslate_ui()
        super().changeEvent(event)

    def _setup_ui(self):
        """Constructs the user interface widgets and layouts for this tab."""
        main_layout = QVBoxLayout(self)
        grid_layout = QGridLayout()

        # --- Primary Motor Settings ---
        self.primary_group = QGroupBox()
        primary_layout = QFormLayout(self.primary_group)
        self.label_pole_pairs = QLabel()
        self.motor_pole_pairs = QLineEdit()
        self.label_torque_const = QLabel()
        self.motor_torque_const = QLineEdit()
        self.label_motor_type = QLabel()
        self.motor_type = QComboBox()
        for name, value in MOTOR_TYPES.items(): self.motor_type.addItem(name, value)
        self.label_control_mode = QLabel()
        self.control_mode = QComboBox()
        for name, value in CONTROL_MODES.items(): self.control_mode.addItem(name, value)
        primary_layout.addRow(self.label_pole_pairs, self.motor_pole_pairs)
        primary_layout.addRow(self.label_torque_const, self.motor_torque_const)
        primary_layout.addRow(self.label_motor_type, self.motor_type)
        primary_layout.addRow(self.label_control_mode, self.control_mode)

        # --- Limits and Control Settings ---
        self.limits_group = QGroupBox()
        limits_layout = QVBoxLayout(self.limits_group)
        inputs_grid_layout = QGridLayout()
        self.label_max_current = QLabel()
        self.motor_current_lim = QLineEdit()
        self.label_bandwidth = QLabel()
        self.motor_control_bandwidth = QLineEdit()
        self.label_elec_power_thresh = QLabel()
        self.spinout_electrical = QLineEdit()
        self.label_mech_power_thresh = QLabel()
        self.spinout_mechanical = QLineEdit()
        inputs_grid_layout.addWidget(self.label_max_current, 0, 0)
        inputs_grid_layout.addWidget(self.motor_current_lim, 0, 1)
        inputs_grid_layout.addWidget(self.label_bandwidth, 0, 2)
        inputs_grid_layout.addWidget(self.motor_control_bandwidth, 0, 3)
        inputs_grid_layout.addWidget(self.label_elec_power_thresh, 1, 0)
        inputs_grid_layout.addWidget(self.spinout_electrical, 1, 1, 1, 3)
        inputs_grid_layout.addWidget(self.label_mech_power_thresh, 2, 0)
        inputs_grid_layout.addWidget(self.spinout_mechanical, 2, 1, 1, 3)
        limits_layout.addLayout(inputs_grid_layout)
        self.vel_limit_check = QCheckBox()
        self.torque_mode_vel_limit_check = QCheckBox()
        self.overspeed_error_check = QCheckBox()
        limits_layout.addWidget(self.vel_limit_check)
        limits_layout.addWidget(self.torque_mode_vel_limit_check)
        limits_layout.addWidget(self.overspeed_error_check)
        
        # --- Motor Calibration Section ---
        self.calibration_group = QGroupBox()
        calibration_layout = QGridLayout(self.calibration_group)
        self.motor_calibration_current = QLineEdit()
        self.motor_calibration_voltage = QLineEdit()
        status_layout = QHBoxLayout()
        self.label_calib_status = QLabel()
        self.calibration_status_indicator = QLabel()
        self.calibration_status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.calibration_status_indicator.setMinimumWidth(110)
        status_layout.addWidget(self.label_calib_status)
        status_layout.addWidget(self.calibration_status_indicator)
        status_layout.addStretch()
        self.calibrate_motor_button = QPushButton()
        self.motor_pre_calibrated_check = QCheckBox()
        self.label_calib_current = QLabel()
        self.label_calib_voltage = QLabel()
        calibration_layout.addLayout(status_layout, 0, 0, 1, 2)
        calibration_layout.addWidget(self.label_calib_current, 1, 0)
        calibration_layout.addWidget(self.motor_calibration_current, 1, 1)
        calibration_layout.addWidget(self.label_calib_voltage, 2, 0)
        calibration_layout.addWidget(self.motor_calibration_voltage, 2, 1)
        calibration_layout.addWidget(self.calibrate_motor_button, 1, 2)
        calibration_layout.addWidget(self.motor_pre_calibrated_check, 2, 2)

        # --- Layout Assembly ---
        grid_layout.addWidget(self.primary_group, 0, 0)
        grid_layout.addWidget(self.limits_group, 0, 1)
        grid_layout.addWidget(self.calibration_group, 1, 0, 1, 2)
        main_layout.addLayout(grid_layout)
        main_layout.addStretch()
        self.apply_btn = QPushButton()
        self.apply_btn.clicked.connect(self.apply_config)
        main_layout.addWidget(self.apply_btn, 0, Qt.AlignmentFlag.AlignRight)

        # --- Input Validators ---
        c_locale = QLocale(QLocale.Language.C)
        int_validator = QIntValidator(1, 1000, self)
        float_validator = QDoubleValidator(0.0, 9999.0, 4, self)
        float_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        float_validator.setLocale(c_locale)
        self.motor_pole_pairs.setValidator(int_validator)
        self.motor_torque_const.setValidator(float_validator)
        self.motor_current_lim.setValidator(float_validator)
        self.motor_control_bandwidth.setValidator(float_validator)
        self.motor_calibration_current.setValidator(float_validator)
        self.motor_calibration_voltage.setValidator(float_validator)
        self.spinout_electrical.setValidator(float_validator)
        self.spinout_mechanical.setValidator(float_validator)
        
        # --- Signal Connections ---
        self.calibrate_motor_button.clicked.connect(self.start_calibration)
        self.motor_pre_calibrated_check.toggled.connect(self.set_pre_calibrated)

    # --- MUDANÇA: Adiciona a nova função retranslate_ui ---
    def retranslate_ui(self):
        """Updates all translatable texts in this tab."""
        self.primary_group.setTitle(self.tr("Main Settings (Axis 0)"))
        self.motor_pole_pairs.setToolTip(self.tr("The number of magnetic pole pairs of the motor.\nThis is a CRITICAL parameter."))
        self.motor_torque_const.setToolTip(self.tr("The motor's torque constant in Nm/A."))
        self.motor_type.setToolTip(self.tr("Defines the type of motor connected."))
        self.control_mode.setToolTip(self.tr("Defines the control mode activated on startup if 'Closed-Loop Control on Startup' is enabled."))
        self.label_pole_pairs.setText(self.tr("Pole Pairs:"))
        self.label_torque_const.setText(self.tr("Torque Constant (Nm/A):"))
        self.label_motor_type.setText(self.tr("Motor Type:"))
        self.label_control_mode.setText(self.tr("Default Control Mode:"))

        self.limits_group.setTitle(self.tr("Limits and Control"))
        self.label_max_current.setText(self.tr("Max Current (A):"))
        self.label_bandwidth.setText(self.tr("Bandwidth (Hz):"))
        self.label_elec_power_thresh.setText(self.tr("Elec. Power Thresh (W):"))
        self.label_mech_power_thresh.setText(self.tr("Mech. Power Thresh (W):"))
        self.vel_limit_check.setText(self.tr("Disable General Velocity Limit"))
        self.torque_mode_vel_limit_check.setText(self.tr("Disable Vel. Limit (Torque Mode)"))
        self.overspeed_error_check.setText(self.tr("Disable Overspeed Error"))
        self.motor_current_lim.setToolTip(self.tr("The maximum current the ODrive can command to the motor."))
        self.motor_control_bandwidth.setToolTip(self.tr("Defines the responsiveness of the current controller."))
        self.spinout_electrical.setToolTip(self.tr("Threshold for detecting motor spinout based on electrical power."))
        self.spinout_mechanical.setToolTip(self.tr("Threshold for detecting motor spinout based on mechanical power."))
        self.vel_limit_check.setToolTip(self.tr("Disables the general velocity limit (controller.config.vel_limit)."))
        self.torque_mode_vel_limit_check.setToolTip(self.tr("In torque control mode, ODrive still enforces a velocity limit for safety."))
        self.overspeed_error_check.setToolTip(self.tr("Disables the error when motor speed exceeds vel_limit * 1.2."))

        self.calibration_group.setTitle(self.tr("Motor Calibration"))
        self.label_calib_status.setText(self.tr("Calibration Status:"))
        self.label_calib_current.setText(self.tr("Calibration Current (A):"))
        self.label_calib_voltage.setText(self.tr("Calibration Voltage (V):"))
        self.calibrate_motor_button.setText(self.tr("Calibrate Motor Now"))
        self.motor_pre_calibrated_check.setText(self.tr("Save Motor Calibration (Pre-Calibrated)"))
        self.motor_calibration_current.setToolTip(self.tr("Current used during the calibration routine."))
        self.motor_calibration_voltage.setToolTip(self.tr("Max voltage allowed during resistance measurement in calibration."))
        self.calibrate_motor_button.setToolTip(self.tr("Starts the motor calibration routine."))
        self.motor_pre_calibrated_check.setToolTip(self.tr("If checked, ODrive skips motor calibration on startup."))
        self.apply_btn.setText(self.tr("Apply Motor Settings"))

        # Also update dynamic status labels
        odrv = self.get_odrv()
        self.update_motor_calibration_status(odrv.axis0.motor.is_calibrated if odrv else False)

    def update_motor_calibration_status(self, is_calibrated):
        """Updates the visual status indicator for motor calibration."""
        if is_calibrated:
            self.calibration_status_indicator.setText(self.tr("CALIBRATED"))
            style = f"background-color: {AppColors.STATUS_CALIBRATED_BG}; color: {AppColors.STATUS_TEXT}; border-radius: 0px; padding: 2px 4px; font-weight: bold;"
        else:
            self.calibration_status_indicator.setText(self.tr("NOT CALIBRATED"))
            style = f"background-color: {AppColors.STATUS_NOT_CALIBRATED_BG}; color: {AppColors.STATUS_TEXT}; border-radius: 0px; padding: 2px 4px; font-weight: bold;"
        self.calibration_status_indicator.setStyleSheet(style)
            
    def set_pre_calibrated(self, checked):
        """Slot to handle the 'pre_calibrated' checkbox state change and apply it directly."""
        odrv = self.get_odrv()
        if not odrv: 
            self.motor_pre_calibrated_check.setChecked(not checked) # Revert UI change
            return
        try:
            odrv.axis0.motor.config.pre_calibrated = checked
            status_text = self.tr("enabled") if checked else self.tr("disabled")
            message = self.tr("Motor pre-calibrated mode {}.").format(status_text)
            self.main_window.show_status_message(message, AppColors.INFO, 3000)
        except Exception as e:
            error_message = self.tr("Could not set pre-calibrated state: {}").format(e)
            QMessageBox.critical(self, self.tr("Error"), error_message)
            self.motor_pre_calibrated_check.setChecked(not checked) # Revert UI change on error

    def start_calibration(self):
        """Initiates the motor calibration sequence in a background thread."""
        odrv = self.get_odrv()
        if not odrv:
            QMessageBox.warning(self, self.tr("Warning"), self.tr("ODrive not connected. Cannot calibrate."))
            return
        if not self.apply_config(return_on_error=True):
            return
            
        self.calibrate_motor_button.setEnabled(False)
        self.calibrate_motor_button.setText(self.tr(AppMessages.CALIBRATING))
        
        self.calib_thread = QThread()
        self.calib_worker = MotorCalibrationWorker(odrv)
        self.calib_worker.moveToThread(self.calib_thread)
        
        self.calib_thread.started.connect(self.calib_worker.run)
        self.calib_worker.finished.connect(self.calib_thread.quit)
        self.calib_worker.finished.connect(self.calib_worker.deleteLater)
        self.calib_thread.finished.connect(self.calib_thread.deleteLater)
        self.calib_worker.result.connect(self.on_calibration_result)
        self.calib_thread.start()

    def on_calibration_result(self, success, message):
        """Handles the result of the motor calibration worker."""
        self.calibrate_motor_button.setEnabled(True)
        self.calibrate_motor_button.setText(self.tr("Calibrate Motor Now"))
        if success:
            QMessageBox.information(self, self.tr(AppMessages.CALIBRATION_SUCCESS), message)
            self.main_window.populate_all_fields() # Refresh all fields to show new values
        else:
            QMessageBox.critical(self, self.tr(AppMessages.CALIBRATION_FAILED), message)

    def populate_fields(self):
        """Reads motor configuration from the connected ODrive and updates the UI fields."""
        odrv = self.get_odrv()
        if not odrv: return
        try: self.motor_pre_calibrated_check.toggled.disconnect(self.set_pre_calibrated)
        except (TypeError, RuntimeError): pass
        
        self.motor_pole_pairs.setText(str(odrv.axis0.motor.config.pole_pairs))
        self.motor_torque_const.setText(f"{odrv.axis0.motor.config.torque_constant:.4f}")
        index = self.motor_type.findData(odrv.axis0.motor.config.motor_type)
        if index != -1: self.motor_type.setCurrentIndex(index)
        self.motor_current_lim.setText(f"{odrv.axis0.motor.config.current_lim:.2f}")
        self.motor_control_bandwidth.setText(f"{odrv.axis0.motor.config.current_control_bandwidth:.2f}")
        index_control = self.control_mode.findData(odrv.axis0.controller.config.control_mode)
        if index_control != -1: self.control_mode.setCurrentIndex(index_control)
        self.spinout_electrical.setText(f"{odrv.axis0.controller.config.spinout_electrical_power_threshold:.2f}")
        self.spinout_mechanical.setText(f"{odrv.axis0.controller.config.spinout_mechanical_power_threshold:.2f}")
        self.vel_limit_check.setChecked(not odrv.axis0.controller.config.enable_vel_limit)
        self.torque_mode_vel_limit_check.setChecked(not odrv.axis0.controller.config.enable_torque_mode_vel_limit)
        self.overspeed_error_check.setChecked(not odrv.axis0.controller.config.enable_overspeed_error)
        self.motor_calibration_current.setText(f"{odrv.axis0.motor.config.calibration_current:.2f}")
        self.motor_calibration_voltage.setText(f"{odrv.axis0.motor.config.resistance_calib_max_voltage:.2f}")
        self.motor_pre_calibrated_check.setChecked(odrv.axis0.motor.config.pre_calibrated)
        self.update_motor_calibration_status(odrv.axis0.motor.is_calibrated)
        self.motor_pre_calibrated_check.toggled.connect(self.set_pre_calibrated)

    def apply_config(self, return_on_error=False):
        """Applies the settings from the UI fields to the connected ODrive."""
        odrv = self.get_odrv()
        if not odrv: return False
        try:
            odrv.axis0.motor.config.pole_pairs = int(self.motor_pole_pairs.text())
            odrv.axis0.motor.config.torque_constant = float(self.motor_torque_const.text().replace(',', '.'))
            odrv.axis0.motor.config.motor_type = self.motor_type.currentData()
            odrv.axis0.motor.config.current_lim = float(self.motor_current_lim.text().replace(',', '.'))
            odrv.axis0.motor.config.current_control_bandwidth = float(self.motor_control_bandwidth.text().replace(',', '.'))
            odrv.axis0.controller.config.control_mode = self.control_mode.currentData()
            odrv.axis0.controller.config.spinout_electrical_power_threshold = float(self.spinout_electrical.text().replace(',', '.'))
            odrv.axis0.controller.config.spinout_mechanical_power_threshold = float(self.spinout_mechanical.text().replace(',', '.'))
            odrv.axis0.controller.config.enable_vel_limit = not self.vel_limit_check.isChecked()
            odrv.axis0.controller.config.enable_torque_mode_vel_limit = not self.torque_mode_vel_limit_check.isChecked()
            odrv.axis0.controller.config.enable_overspeed_error = not self.overspeed_error_check.isChecked()
            odrv.axis0.motor.config.calibration_current = float(self.motor_calibration_current.text().replace(',', '.'))
            odrv.axis0.motor.config.resistance_calib_max_voltage = float(self.motor_calibration_voltage.text().replace(',', '.'))
            
            self.main_window.show_status_message(self.tr("Motor settings applied."), AppColors.SUCCESS, 3000)
            return True
        except ValueError:
            QMessageBox.critical(self, self.tr("Input Error"), self.tr("Invalid values in fields. Please check that all numbers are correct and not empty."))
            if return_on_error: return False
        except Exception as e:
            error_message = self.tr("Error applying Motor config: {}").format(e)
            self.main_window.show_status_message(error_message, AppColors.ERROR, 5000)
            if return_on_error: return False
        return False # Ensure a boolean is always returned