# tabs/dc_tab.py
"""
This module defines the DCTab class, which provides a user interface for configuring
the DC power source settings of the ODrive, including voltage and current limits,
and brake resistor configuration.
"""
from PySide6.QtWidgets import (
    QLabel, QLineEdit, QPushButton, QVBoxLayout, QFormLayout, 
    QGroupBox, QCheckBox, QMessageBox, QHBoxLayout
)
from PySide6.QtGui import QDoubleValidator
# QEvent é necessário para a tradução dinâmica ---
from PySide6.QtCore import Qt, QLocale, QEvent
import math

from .base_tab import BaseTab
from app_config import AppColors, AppMessages

class DCTab(BaseTab):
    """
    Manages the UI tab for DC power source configuration.
    """
    def __init__(self, main_window, parent=None):
        """Initializes the DCTab, setting up UI and initial state."""
        super().__init__(main_window, parent)
        self._setup_ui()
        # Chama a re-tradução na inicialização ---
        self.retranslate_ui()

    # Adiciona o método changeEvent ---
    def changeEvent(self, event):
        """Catches language change events to re-translate the UI."""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslate_ui()
        super().changeEvent(event)

    def toggle_brake_resistor_field(self, checked):
        """Enables or disables the brake resistor text field based on the checkbox state."""
        self.brake_resistor_value.setEnabled(checked)

    def _setup_ui(self):
        """Constructs the user interface widgets and layouts for this tab."""
        main_layout = QVBoxLayout(self)

        # --- Voltage Limits Section ---
        self.voltage_group = QGroupBox()
        voltage_layout = QFormLayout(self.voltage_group)
        self.label_vbus_min = QLabel()
        self.vbus_voltage_min = QLineEdit()
        self.label_vbus_max = QLabel()
        self.vbus_voltage_max = QLineEdit()
        voltage_layout.addRow(self.label_vbus_min, self.vbus_voltage_min)
        voltage_layout.addRow(self.label_vbus_max, self.vbus_voltage_max)

        # --- Current Limits Section ---
        self.current_group = QGroupBox()
        current_layout = QFormLayout(self.current_group)
        self.label_dc_max_pos = QLabel()
        self.dc_max_positive = QLineEdit()
        self.label_dc_max_neg = QLabel()
        self.dc_max_negative = QLineEdit()
        self.label_max_regen = QLabel()
        self.max_regen_current = QLineEdit()
        self.no_dc_pos_limit_check = QCheckBox()
        dc_pos_layout = QHBoxLayout()
        dc_pos_layout.addWidget(self.dc_max_positive)
        dc_pos_layout.addWidget(self.no_dc_pos_limit_check)
        current_layout.addRow(self.label_dc_max_pos, dc_pos_layout)
        current_layout.addRow(self.label_dc_max_neg, self.dc_max_negative)
        current_layout.addRow(self.label_max_regen, self.max_regen_current)

        # --- Braking Settings Section ---
        self.braking_group = QGroupBox()
        braking_layout = QFormLayout(self.braking_group)
        self.label_brake_res = QLabel()
        self.brake_resistor_value = QLineEdit()
        self.enable_brake_resistor_check = QCheckBox()
        braking_layout.addRow(self.enable_brake_resistor_check)
        braking_layout.addRow(self.label_brake_res, self.brake_resistor_value)
        self.brake_resistor_value.setEnabled(False) # Start disabled
        
        # --- Layout Assembly ---
        self.apply_btn = QPushButton()
        self.apply_btn.clicked.connect(self.apply_config)
        main_layout.addWidget(self.voltage_group)
        main_layout.addWidget(self.current_group)
        main_layout.addWidget(self.braking_group)
        main_layout.addStretch()
        main_layout.addWidget(self.apply_btn, 0, Qt.AlignmentFlag.AlignRight)

        # --- Input Validators ---
        c_locale = QLocale(QLocale.Language.C)
        float_validator = QDoubleValidator(0.0, 9999.0, 4, self)
        float_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        float_validator.setLocale(c_locale)
        negative_float_validator = QDoubleValidator(-9999.0, 0.0, 4, self)
        negative_float_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        negative_float_validator.setLocale(c_locale)
        self.vbus_voltage_min.setValidator(float_validator)
        self.vbus_voltage_max.setValidator(float_validator)
        self.dc_max_positive.setValidator(float_validator)
        self.max_regen_current.setValidator(float_validator)
        self.brake_resistor_value.setValidator(float_validator)
        self.dc_max_negative.setValidator(negative_float_validator)
        
        # --- Signal Connections ---
        self.enable_brake_resistor_check.toggled.connect(self.toggle_brake_resistor_field)
        self.no_dc_pos_limit_check.toggled.connect(self.toggle_dc_pos_limit)

    # Adiciona a nova função retranslate_ui ---
    def retranslate_ui(self):
        """Updates all translatable texts in this tab."""
        self.voltage_group.setTitle(self.tr("DC Bus Voltage Limits"))
        self.label_vbus_min.setText(self.tr("Minimum Voltage (V):"))
        self.label_vbus_max.setText(self.tr("Maximum Voltage (V):"))
        self.current_group.setTitle(self.tr("DC Bus Current Limits"))
        self.no_dc_pos_limit_check.setText(self.tr("No Limit"))
        self.label_dc_max_pos.setText(self.tr("Max Positive DC Current (A):"))
        self.label_dc_max_neg.setText(self.tr("Max Negative DC Current (A):"))
        self.label_max_regen.setText(self.tr("Max Regen Current (A):"))
        self.braking_group.setTitle(self.tr("Braking Settings"))
        self.enable_brake_resistor_check.setText(self.tr("Enable Brake Resistor"))
        self.label_brake_res.setText(self.tr("Brake Resistance (Ω):"))
        self.apply_btn.setText(self.tr("Apply Power Source Settings"))

    def toggle_dc_pos_limit(self, checked):
        """Handles the logic for the 'No Limit' checkbox for positive DC current."""
        self.dc_max_positive.setEnabled(not checked)
        if checked: 
            self.dc_max_positive.setText(self.tr("Infinite"))
        else:
            odrv = self.get_odrv()
            if odrv:
                current_val = odrv.config.dc_max_positive_current
                self.dc_max_positive.setText("10.0" if math.isinf(current_val) else f"{current_val:.2f}")

    def populate_fields(self):
        """Reads DC power settings from the connected ODrive and updates the UI fields."""
        odrv = self.get_odrv()
        if not odrv: return
        
        self.vbus_voltage_min.setText(f"{odrv.config.dc_bus_undervoltage_trip_level:.2f}")
        self.vbus_voltage_max.setText(f"{odrv.config.dc_bus_overvoltage_trip_level:.2f}")
        
        dc_pos_current = odrv.config.dc_max_positive_current
        is_inf = math.isinf(dc_pos_current)
        self.no_dc_pos_limit_check.setChecked(is_inf)
        self.dc_max_positive.setEnabled(not is_inf)
        self.dc_max_positive.setText(self.tr("Infinite") if is_inf else f"{dc_pos_current:.2f}")
        
        self.dc_max_negative.setText(f"{odrv.config.dc_max_negative_current:.2f}")
        self.max_regen_current.setText(f"{odrv.config.max_regen_current:.2f}")
        self.brake_resistor_value.setText(f"{odrv.config.brake_resistance:.2f}")
        
        is_brake_enabled = odrv.config.enable_brake_resistor
        self.enable_brake_resistor_check.setChecked(is_brake_enabled)
        self.toggle_brake_resistor_field(is_brake_enabled) # Synchronize UI state

    def apply_config(self):
        """Applies the settings from the UI fields to the connected ODrive."""
        odrv = self.get_odrv()
        if not odrv: return
        try:
            odrv.config.dc_bus_undervoltage_trip_level = float(self.vbus_voltage_min.text().replace(',', '.'))
            odrv.config.dc_bus_overvoltage_trip_level = float(self.vbus_voltage_max.text().replace(',', '.'))
            
            if self.no_dc_pos_limit_check.isChecked():
                odrv.config.dc_max_positive_current = float('inf')
            else:
                odrv.config.dc_max_positive_current = float(self.dc_max_positive.text().replace(',', '.'))
            
            odrv.config.dc_max_negative_current = float(self.dc_max_negative.text().replace(',', '.'))
            odrv.config.max_regen_current = float(self.max_regen_current.text().replace(',', '.'))
            odrv.config.brake_resistance = float(self.brake_resistor_value.text().replace(',', '.'))
            odrv.config.enable_brake_resistor = self.enable_brake_resistor_check.isChecked()
            
            self.main_window.show_status_message(self.tr("Power source settings applied."), AppColors.SUCCESS, 3000)
            QMessageBox.information(self, self.tr("Reminder"), 
                                     f"{self.tr(AppMessages.CONFIG_APPLY_SUCCESS)}.\n\n{self.tr(AppMessages.SAVE_REMINDER)}")
        except ValueError:
            QMessageBox.critical(self, self.tr("Input Error"), self.tr("Invalid values in fields. Please check that all numbers are correct and not empty."))
        except Exception as e:
            error_message = self.tr("Error applying power source settings: {}").format(e)
            self.main_window.show_status_message(error_message, AppColors.ERROR, 5000)