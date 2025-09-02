# tabs/backup_tab.py
"""
This module defines the BackupTab class, which provides a user interface for
exporting (backing up) and importing (restoring) the ODrive configuration to/from a JSON file.
"""
import json
import os
import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel, QTextEdit, 
    QMessageBox, QFileDialog
)
# --- MUDANÇA: QEvent é necessário para a tradução dinâmica ---
from PySide6.QtCore import Qt, QEvent

from .base_tab import BaseTab
from app_config import AppColors, AppMessages

class BackupTab(BaseTab):
    """
    Manages the UI tab for backing up and restoring ODrive settings.
    """
    def __init__(self, main_window, parent=None):
        """Initializes the BackupTab, setting up UI and initial state."""
        super().__init__(main_window, parent)
        self._setup_ui()
        self.on_connection_status_changed(False)
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
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- Backup Section (Export) ---
        self.backup_group = QGroupBox()
        backup_layout = QHBoxLayout(self.backup_group)
        backup_layout.setSpacing(15)
        self.backup_button = QPushButton()
        self.backup_button.clicked.connect(self.run_backup)
        self.backup_button.setMinimumHeight(40)
        self.backup_button.setFixedWidth(250)
        self.backup_info = QLabel()
        self.backup_info.setWordWrap(True)
        backup_layout.addWidget(self.backup_button)
        backup_layout.addWidget(self.backup_info, 1)

        # --- Restore Section (Import) ---
        self.restore_group = QGroupBox()
        restore_layout = QHBoxLayout(self.restore_group)
        restore_layout.setSpacing(15)
        self.restore_button = QPushButton()
        self.restore_button.clicked.connect(self.run_restore)
        self.restore_button.setMinimumHeight(40)
        self.restore_button.setFixedWidth(250)
        self.restore_info = QLabel()
        self.restore_info.setStyleSheet(f"color: {AppColors.WARNING};")
        self.restore_info.setWordWrap(True)
        restore_layout.addWidget(self.restore_button)
        restore_layout.addWidget(self.restore_info, 1)
        
        # --- Log Section ---
        self.log_group = QGroupBox()
        log_layout = QVBoxLayout(self.log_group)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)
        
        main_layout.addWidget(self.backup_group)
        main_layout.addWidget(self.restore_group)
        main_layout.addWidget(self.log_output, 1)

    # --- MUDANÇA: Adiciona a nova função retranslate_ui ---
    def retranslate_ui(self):
        """Updates all translatable texts in this tab."""
        self.backup_group.setTitle(self.tr("Backup Configuration"))
        self.backup_button.setText(self.tr("Export Configuration to JSON..."))
        self.backup_info.setText(self.tr("Save all current ODrive settings to a JSON file. This is the most reliable method and works with all firmware versions."))
        self.restore_group.setTitle(self.tr("Restore Configuration"))
        self.restore_button.setText(self.tr("Import Configuration from JSON..."))
        self.restore_info.setText(self.tr("<b>Warning:</b> This will overwrite all settings on the ODrive. This action cannot be undone."))
        self.log_group.setTitle(self.tr("Log"))
        self.on_connection_status_changed(self.main_window.is_connected) # Updates placeholder text

    def _get_config_recursive(self, obj):
        """
        Recursively traverses the ODrive object tree to build a dictionary of configuration parameters,
        ignoring read-only, volatile, or problematic attributes.
        """
        config = {}
        ignored_attrs = [
            'parent', 'endpoint_names', 'channel', 'endpoints', 'remote_endpoint_operation_aborted', 
            'disarmed_reason', 'brake_resistor_armed', 'brake_resistor_current', 'brake_resistor_saturated',
            'error', 'fw_version_major', 'fw_version_minor', 'fw_version_revision', 'fw_version_unreleased',
            'hw_version_major', 'hw_version_minor', 'hw_version_variant', 'ibus', 'ibus_report_filter_k', 
            'misconfigured', 'n_evt_control_loop', 'n_evt_sampling', 'otp_valid', 'serial_number', 
            'task_timers_armed', 'test_property', 'user_config_loaded', 'vbus_voltage', 'system_stats',
            'current_state', 'requested_state'
        ]
        for key in dir(obj):
            if key.startswith('_') or key in ignored_attrs:
                continue
            try:
                val = getattr(obj, key)
                if callable(val): continue
                if isinstance(val, float):
                    if math.isinf(val): config[key] = "Infinity" if val > 0 else "-Infinity"
                    elif math.isnan(val): config[key] = "NaN"
                    else: config[key] = val
                elif isinstance(val, (int, bool, str)):
                    config[key] = val
                else:
                    nested_config = self._get_config_recursive(val)
                    if nested_config: config[key] = nested_config
            except Exception:
                continue
        return config

    def _set_config_from_dict(self, obj, config_dict):
        """Recursively applies configuration values from a dictionary to the ODrive object."""
        for key, val in config_dict.items():
            try:
                if isinstance(val, dict):
                    if hasattr(obj, key): self._set_config_from_dict(getattr(obj, key), val)
                else:
                    if isinstance(val, str):
                        if val == 'Infinity': val = float('inf')
                        elif val == '-Infinity': val = float('-inf')
                        elif val == 'NaN': val = float('nan')
                    if hasattr(obj, key): setattr(obj, key, val)
            except Exception:
                continue

    def run_backup(self):
        """Handles the logic for exporting the ODrive configuration to a JSON file."""
        odrv = self.get_odrv()
        if not odrv: return

        filename, _ = QFileDialog.getSaveFileName(self, self.tr("Save Configuration Backup"), "", self.tr("JSON Config Files (*.json);;All Files (*)"))
        if not filename:
            self.log_output.append(self.tr("Backup canceled by user."))
            return
        try:
            self.log_output.append(self.tr("Reading full configuration from ODrive..."))
            full_config = {}
            config_branches = ['config', 'axis0', 'axis1', 'can']
            for branch_name in config_branches:
                if hasattr(odrv, branch_name):
                    log_msg = self.tr("  - Backing up '{0}'...").format(branch_name)
                    self.log_output.append(log_msg)
                    branch_obj = getattr(odrv, branch_name)
                    full_config[branch_name] = self._get_config_recursive(branch_obj)
            
            log_msg = self.tr("Saving backup to: {0}...").format(os.path.basename(filename))
            self.log_output.append(log_msg)
            with open(filename, 'w') as f:
                json.dump(full_config, f, indent=2)
            
            self.log_output.append(self.tr("<b>Backup completed successfully!</b>"))
            success_msg = self.tr("Configuration successfully saved to:\n{0}").format(filename)
            QMessageBox.information(self, self.tr("Success"), success_msg)
        except Exception as e:
            error_msg = self.tr("<b>Backup failed:</b> {0}").format(e)
            self.log_output.append(error_msg)
            critical_msg = self.tr("Failed to save configuration.\n\n{0}").format(e)
            QMessageBox.critical(self, self.tr("Error"), critical_msg)

    def run_restore(self):
        """Handles the logic for importing a configuration from a JSON file to the ODrive."""
        odrv = self.get_odrv()
        if not odrv: return

        reply = QMessageBox.warning(self, self.tr("Confirm Restore"), 
                                    self.tr("This will overwrite all current settings on the ODrive.\n"
                                            "This action is irreversible.\n\n"
                                            "Are you sure you want to continue?"), 
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                    QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            self.log_output.append(self.tr("Restore canceled by user."))
            return

        filename, _ = QFileDialog.getOpenFileName(self, self.tr("Restore Configuration Backup"), "", 
                                                  self.tr("JSON Config Files (*.json);;All Files (*)"))
        if not filename:
            self.log_output.append(self.tr("Restore file selection canceled by user."))
            return
        try:
            log_msg = self.tr("Reading configuration from: {0}...").format(os.path.basename(filename))
            self.log_output.append(log_msg)
            with open(filename, 'r') as f:
                config_dict = json.load(f)
            
            self.log_output.append(self.tr("Applying configuration to ODrive. This may take a moment..."))
            self._set_config_from_dict(odrv, config_dict)
            self.log_output.append(self.tr("<b>Restore completed successfully!</b>"))
            self.main_window.populate_all_fields()
            
            success_message_html = (
                self.tr("Configuration successfully restored from:<br>{0}<br><br>").format(filename) +
                self.tr("<b>Important:</b> After restoring, you <b>must</b> perform a "
                        "full encoder calibration before operating the motor.<br><br>") +
                self.tr(AppMessages.SAVE_REMINDER)
            )
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(self.tr("Success"))
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setTextFormat(Qt.TextFormat.RichText)
            msg_box.setText(success_message_html)
            msg_box.exec()
        except json.JSONDecodeError as e:
            error_msg = self.tr("<b>Restore failed:</b> Invalid JSON file format. {0}").format(e)
            self.log_output.append(error_msg)
            critical_msg = self.tr("Could not restore configuration.\n"
                                   "The selected file is not a valid JSON file.\n\n{0}").format(e)
            QMessageBox.critical(self, self.tr("Error"), critical_msg)
        except Exception as e:
            error_msg = self.tr("<b>Restore failed:</b> {0}").format(e)
            self.log_output.append(error_msg)
            critical_msg = self.tr("Failed to restore configuration.\n\n{0}").format(e)
            QMessageBox.critical(self, self.tr("Error"), critical_msg)
            
    def on_connection_status_changed(self, is_connected):
        """Enables or disables UI elements based on the ODrive connection status."""
        self.backup_button.setEnabled(is_connected)
        self.restore_button.setEnabled(is_connected)
        placeholder_text = self.tr("Backup and restore process details will appear here.")
        if not is_connected:
            placeholder_text = self.tr("Connect to an ODrive to enable backup and restore.")
        self.log_output.setPlaceholderText(placeholder_text)

    def populate_fields(self):
        """(Not used in this tab) Placeholder for consistency with other tabs."""
        pass

    def apply_config(self):
        """(Not used in this tab) Placeholder for consistency with other tabs."""
        pass