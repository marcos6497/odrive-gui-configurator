# main.py
"""
This is the main entry point for the ODrive GUI Configurator application.
It sets up the main window, manages ODrive connections, and integrates all UI tabs.
"""
import os
os.environ['QT_API'] = 'pyside6'
os.environ['PYQTGRAPH_QT_LIB'] = 'PySide6'

import sys
import io
from contextlib import redirect_stdout
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QTextEdit, QPushButton, QDialog,
    QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QMessageBox, QGroupBox,
    QFileDialog, QStatusBar, QLineEdit, QMenu
)
from PySide6.QtGui import (
    QFont, QColor, QIcon, QPixmap, QGuiApplication, QPalette, QDesktopServices, 
    QAction, QActionGroup
)
from PySide6.QtCore import (
    Qt, QTimer, QThread, QUrl, QTranslator, QLocale, QSettings, QEvent, Signal
)
import qdarkstyle
import odrive
from odrive.utils import dump_errors
from ansi2html import Ansi2HTMLConverter
import fibre

# --- Local Imports ---
from tabs import DCTab, MotorTab, CANTab, EncoderTab, TerminalTab, GraphTab, ODriveWorker, FirmwareTab, BackupTab
from app_config import AppColors, AppMessages, AppConstants

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

ICON_PATH = resource_path(os.path.join('assets', 'odrive_icon.png'))

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.PIX_KEY = "98f0244d-6a9b-4201-a9a0-433db36f16c0"
        self.PAYPAL_URL = "https://www.paypal.com/donate/?business=HTDDRZL6XCVSE&no_recurring=0&currency_code=BRL"
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 10)
        main_layout.setSpacing(10)
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #2a2a2a;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(50, 10, 15, 10)
        icon_label = QLabel()
        pixmap = QPixmap(ICON_PATH)
        if not pixmap.isNull():
            icon_label.setPixmap(pixmap.scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        title_layout = QVBoxLayout()
        self.title_label = QLabel()
        self.title_label.setFont(QFont("Roboto", 16, QFont.Weight.Bold))
        self.dev_label = QLabel()
        self.dev_label.setFont(QFont("Roboto", 10))
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.dev_label)
        header_layout.addWidget(icon_label)
        header_layout.addSpacing(15)
        header_layout.addLayout(title_layout)
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(15, 10, 15, 10)
        body_layout.setSpacing(10)
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        self.links_group = QGroupBox()
        links_layout = QGridLayout(self.links_group)
        self.doc_text_label = QLabel()
        doc_link_label = QLabel('<a href="https://docs.odriverobotics.com">docs.odriverobotics.com</a>')
        doc_link_label.setOpenExternalLinks(True)
        self.contact_text_label = QLabel()
        telegram_link_label = QLabel('<a href="https://t.me/silvamarcos1">@silvamarcos1</a>')
        telegram_link_label.setOpenExternalLinks(True)
        links_layout.addWidget(self.doc_text_label, 0, 0); links_layout.addWidget(doc_link_label, 0, 1)
        links_layout.addWidget(self.contact_text_label, 1, 0); links_layout.addWidget(telegram_link_label, 1, 1)
        self.support_group = QGroupBox()
        support_layout = QVBoxLayout(self.support_group)
        self.support_intro_label = QLabel()
        self.pix_key_label = QLabel()
        key_layout = QHBoxLayout()
        self.pix_key_field = QLineEdit(self.PIX_KEY) 
        self.pix_key_field.setReadOnly(True); self.pix_key_field.setFont(QFont("Consolas", 9))
        self.pix_key_field.setStyleSheet("background-color: #2c2c2c; border: 1px solid #444;")
        self.copy_button = QPushButton()
        self.copy_button.clicked.connect(self.copy_pix_to_clipboard)
        key_layout.addWidget(self.pix_key_field); key_layout.addWidget(self.copy_button)
        self.paypal_button = QPushButton()
        self.paypal_button.clicked.connect(self.open_paypal_link)
        support_layout.addWidget(self.support_intro_label)
        support_layout.addWidget(self.pix_key_label)
        support_layout.addLayout(key_layout)
        support_layout.addSpacing(10)
        support_layout.addWidget(self.paypal_button)
        body_layout.addWidget(self.desc_label)
        body_layout.addWidget(self.links_group)
        body_layout.addWidget(self.support_group)
        body_layout.addStretch()
        button_layout = QHBoxLayout()
        self.licenses_button = QPushButton()
        self.licenses_button.clicked.connect(self.open_licenses_file)
        self.licenses_button.setFixedSize(100, 28)
        self.close_button = QPushButton()
        self.close_button.clicked.connect(self.accept)
        self.close_button.setFixedSize(100, 28)
        button_layout.addStretch()
        button_layout.addWidget(self.licenses_button)
        button_layout.addSpacing(10)
        button_layout.addWidget(self.close_button)
        button_layout.addStretch()
        main_layout.addWidget(header_widget)
        main_layout.addWidget(body_widget)
        main_layout.addLayout(button_layout)
        self.setMinimumWidth(480) 
        self.adjustSize()
        self.setFixedSize(self.size())
        self.retranslate_ui()
    def retranslate_ui(self):
        self.setWindowTitle(self.tr("About ODrive GUI Configurator"))
        self.title_label.setText(self.tr("ODrive GUI Configurator"))
        self.dev_label.setText(self.tr("Developed by <b>Marcos Silva</b>"))
        self.desc_label.setText(self.tr("This application was created to facilitate the configuration and monitoring of ODrive boards."))
        self.links_group.setTitle(self.tr("Useful Links"))
        self.doc_text_label.setText(self.tr("Official Documentation:"))
        self.contact_text_label.setText(self.tr("Contact (Telegram):"))
        self.support_group.setTitle(self.tr("Support the Project"))
        self.support_intro_label.setText(self.tr("Did I help you in any way? Consider sending a donation :)"))
        self.pix_key_label.setText(self.tr("PIX Key (Brazil):"))
        self.copy_button.setText(self.tr("Copy"))
        self.paypal_button.setText(self.tr("Donate with PayPal"))
        self.licenses_button.setText(self.tr("Licenses"))
        self.close_button.setText(self.tr("Close"))
    def changeEvent(self, event):
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslate_ui()
        super().changeEvent(event)
    def copy_pix_to_clipboard(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.pix_key_field.text())
        self.copy_button.setText(self.tr("Copied!"))
        QTimer.singleShot(2000, lambda: self.copy_button.setText(self.tr("Copy")))
    def open_paypal_link(self):
        QDesktopServices.openUrl(QUrl(self.PAYPAL_URL))
    def open_licenses_file(self):
        licenses_path = resource_path(os.path.join('licenses', 'NOTICE.txt'))
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(licenses_path))
        except Exception as e:
            print(f"Could not open licenses file: {e}")

class ErrorDialog(QDialog):
    errors_cleared = Signal()
    def __init__(self, html_content, odrv_proxy, parent=None):
        super().__init__(parent)
        self.odrv_proxy = odrv_proxy
        self.setWindowTitle(self.tr("ODrive Error Viewer"))
        self.setMinimumSize(550, 400)
        layout = QVBoxLayout(self)
        label = QLabel(self.tr("Errors found on the ODrive:"))
        self.error_display = QTextEdit()
        palette = self.error_display.palette()
        palette.setColor(palette.ColorRole.Base, QColor("#1e1e1e"))
        self.error_display.setPalette(palette)
        self.error_display.setHtml(html_content)
        self.error_display.setReadOnly(True)
        self.clear_button = QPushButton(self.tr("Clear Errors"))
        self.close_button = QPushButton(self.tr("Close"))
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.close_button)
        layout.addWidget(label)
        layout.addWidget(self.error_display)
        layout.addLayout(button_layout)
        self.clear_button.clicked.connect(self.clear_odrive_errors)
        self.close_button.clicked.connect(self.reject)
    def clear_odrive_errors(self):
        try:
            self.odrv_proxy.odrv.clear_errors()
            QMessageBox.information(self, self.tr("Success"), self.tr("Errors cleared successfully."))
            self.errors_cleared.emit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Could not clear errors.\n\nDetails: {0}").format(e))
            
class ConfigDialog(QDialog):
    def __init__(self, config_text, parent=None):
        super().__init__(parent)
        self.config_text = config_text
        self.setWindowTitle(self.tr("ODrive Configuration Viewer"))
        self.setMinimumSize(600, 500)
        layout = QVBoxLayout(self)
        label = QLabel(self.tr("Full device configuration:"))
        self.config_display = QTextEdit()
        self.config_display.setText(self.config_text)
        self.config_display.setReadOnly(True)
        self.config_display.setFont(QFont("Consolas", 9))
        self.save_button = QPushButton(self.tr("Save to TXT..."))
        self.close_button = QPushButton(self.tr("Close"))
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.close_button)
        layout.addWidget(label)
        layout.addWidget(self.config_display)
        layout.addLayout(button_layout)
        self.save_button.clicked.connect(self.save_to_file)
        self.close_button.clicked.connect(self.reject)
    def save_to_file(self):
        options = QFileDialog.Option.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self, self.tr("Save Configuration"), "odrive_config_dump.txt", "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            try:
                with open(file_name, 'w') as f:
                    f.write(self.config_text)
                QMessageBox.information(self, self.tr("Success"), self.tr("Configuration saved to:\n{0}").format(file_name))
            except Exception as e:
                QMessageBox.critical(self, self.tr("Save Error"), self.tr("Could not save the file.\n\nDetails: {0}").format(e))

class ODriveGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.translator = QTranslator()
        self.setFixedSize(850, 600)
        self.setFont(QFont("Roboto", 10))
        self.AXIS_STATE_MAP = {}
        self.language_map = {'en_US': "English", 'pt_BR': "Português"}
        self.odrv_thread, self.odrv_worker, self.odrv_proxy = None, None, None
        self.is_connected = False
        self.last_tab_index = 0
        self.connect_button, self.show_errors_button = None, None
        self.original_button_style = ""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        top_layout = QHBoxLayout()
        self.connection_group = self.create_connection_panel()
        self.telemetry_group = self.create_telemetry_panel()
        top_layout.addWidget(self.connection_group, 2)
        top_layout.addWidget(self.telemetry_group, 1)
        self.tabs = QTabWidget()
        self.dc_tab = DCTab(self); self.tabs.addTab(self.dc_tab, "")
        self.motor_tab = MotorTab(self); self.tabs.addTab(self.motor_tab, "")
        self.encoder_tab = EncoderTab(self); self.tabs.addTab(self.encoder_tab, "")
        self.can_tab = CANTab(self); self.tabs.addTab(self.can_tab, "")
        self.firmware_tab = FirmwareTab(self); self.tabs.addTab(self.firmware_tab, "")
        self.graph_tab = GraphTab(self); self.tabs.addTab(self.graph_tab, "")
        self.terminal_tab = TerminalTab(self); self.tabs.addTab(self.terminal_tab, "")
        self.backup_tab = BackupTab(self); self.tabs.addTab(self.backup_tab, "")
        self.about_tab_placeholder = QWidget(); self.tabs.addTab(self.about_tab_placeholder, "")
        self.config_tabs = [self.dc_tab, self.motor_tab, self.can_tab, self.encoder_tab, self.firmware_tab]
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.tabs)
        self.setStatusBar(QStatusBar())
        self.statusBar().setSizeGripEnabled(False)
        self.original_statusbar_style = self.statusBar().styleSheet()
        self.create_language_selector_in_statusbar()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.retranslate_ui()
        self.reset_telemetry_labels()

    def retranslate_ui(self):
        self.setWindowTitle(self.tr("ODrive GUI Configurator 1.2"))
        self.setWindowIcon(QIcon(ICON_PATH))
        self.AXIS_STATE_MAP = {
            0: self.tr("UNDEFINED"), 1: self.tr("IDLE"), 2: self.tr("STARTUP SEQUENCE"),
            3: self.tr("FULL CALIBRATION SEQUENCE"), 4: self.tr("MOTOR CALIBRATION"),
            5: self.tr("ENCODER INDEX SEARCH"), 6: self.tr("ENCODER OFFSET CALIBRATION"),   
            7: self.tr("CLOSED LOOP CONTROL"), 8: self.tr("CLOSED_LOOP_CONTROL"),
            9: self.tr("ENCODER DIR FIND"), 10: self.tr("HOMING"),
            11: self.tr("ENCODER HALL POLARITY CALIBRATION"), 12: self.tr("ENCODER HALL PHASE CALIBRATION")
        }
        self.connection_group.setTitle(self.tr("Connection & General Commands"))
        buttons_info = {
            "connect": (self.tr("Connect to ODrive"), None),
            "save": (self.tr("Save Configuration"), self.tr("Executes odrv.save_configuration(). Motor must be in IDLE.")),
            "disconnect": (self.tr("Disconnect from ODrive"), None),
            "show_errors": (self.tr("Show Errors"), None),
            "reboot": (self.tr("Reboot ODrive"), None),
            "set_idle": (self.tr("Set IDLE (Axis 0)"), self.tr("Puts Axis 0 in IDLE state. Required to save configuration.")),
            "erase": (self.tr("Erase Configuration"), self.tr("Restores ODrive to factory settings. This action is irreversible!")),
            "show_config": (self.tr("View Configuration"), self.tr("Shows the full ODrive configuration and allows saving to a file."))
        }
        for key, (text, tooltip) in buttons_info.items():
            button = self.buttons[key]; button.setText(text)
            if tooltip: button.setToolTip(tooltip)
        self.telemetry_group.setTitle(self.tr("Real-Time Telemetry (Axis 0)"))
        if self.is_connected and hasattr(self, 'last_telemetry_data') and self.last_telemetry_data is not None:
            self.update_telemetry_labels(*self.last_telemetry_data)
        else:
            self.reset_telemetry_labels()
        self.tabs.setTabText(0, self.tr("DC Power")); self.tabs.setTabText(1, self.tr("Motor"))
        self.tabs.setTabText(2, self.tr("Encoder")); self.tabs.setTabText(3, self.tr("CAN"))
        self.tabs.setTabText(4, self.tr("Firmware")); self.tabs.setTabText(5, self.tr("Graph"))
        self.tabs.setTabText(6, self.tr("Terminal")); self.tabs.setTabText(7, self.tr("Backup"))
        self.tabs.setTabText(8, self.tr("About"))
        self.show_status_message(self.tr("Ready."))
        settings = QSettings()
        current_locale = settings.value('language', 'en_US')
        current_lang_name = self.tr(self.language_map.get(current_locale, "English"))
        self.language_button.setText(f"🌐 {current_lang_name}")
        self.language_button.setToolTip(self.tr("Change application language"))
        for locale, action in self.language_actions.items():
            action.setText(self.tr(self.language_map[locale]))
        if hasattr(self, 'dc_tab'): self.dc_tab.retranslate_ui()
        if hasattr(self, 'motor_tab'): self.motor_tab.retranslate_ui()
        if hasattr(self, 'encoder_tab'): self.encoder_tab.retranslate_ui()
        if hasattr(self, 'can_tab'): self.can_tab.retranslate_ui()
        if hasattr(self, 'firmware_tab'): self.firmware_tab.retranslate_ui()
        if hasattr(self, 'graph_tab'): self.graph_tab.retranslate_ui()
        if hasattr(self, 'terminal_tab'): self.terminal_tab.retranslate_ui()
        if hasattr(self, 'backup_tab'): self.backup_tab.retranslate_ui()
        
    def changeEvent(self, event):
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslate_ui()
        super().changeEvent(event)

    def create_language_selector_in_statusbar(self):
        settings = QSettings()
        current_locale = settings.value('language', 'en_US')
        self.language_button = QPushButton("", self)
        self.language_button.setFlat(True)
        self.language_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.language_button.setStyleSheet(f"color: {AppColors.NEUTRAL}; margin-right: 5px; padding-right: 10px;")
        menu = QMenu(self)
        action_group = QActionGroup(self)
        action_group.setExclusive(True)
        self.language_actions = {}
        for locale, name in self.language_map.items():
            action = QAction(self.tr(name), self)
            action.setCheckable(True)
            action.setData(locale)
            if locale == current_locale:
                action.setChecked(True)
            menu.addAction(action)
            action_group.addAction(action)
            self.language_actions[locale] = action
        action_group.triggered.connect(self.change_language)
        self.language_button.setMenu(menu)
        self.statusBar().addPermanentWidget(self.language_button)

    def change_language(self, action):
        locale = action.data()
        settings = QSettings()
        settings.setValue('language', locale)
        app = QApplication.instance()
        app.removeTranslator(self.translator)
        if locale != 'en_US':
            translation_file = resource_path(os.path.join('translations', f'{locale}.qm'))
            if self.translator.load(translation_file):
                app.installTranslator(self.translator)
        
    def create_connection_panel(self):
        group = QGroupBox()
        layout = QGridLayout(group)
        self.status_label = QLabel(AppMessages.STATUS_DISCONNECTED)
        self.status_label.setStyleSheet(f"color: {AppColors.ERROR}; font-weight: bold;")
        self.buttons = {}
        buttons_data = [
            ("connect", self.connect_odrive), ("save", self.save_configuration_prompt),
            ("disconnect", self.disconnect_odrive), ("show_errors", self.show_errors),
            ("reboot", self.reboot_odrive), ("set_idle", self.set_axis0_idle),
            ("erase", self.erase_configuration_prompt), ("show_config", self.show_config)
        ]
        layout.addWidget(self.status_label, 0, 0, 1, 2)
        row, col = 1, 0
        for key, func in buttons_data:
            button = QPushButton(); button.clicked.connect(func); self.buttons[key] = button
            if key == "connect": self.connect_button = button
            if key == "show_errors":
                self.show_errors_button = button; self.original_button_style = button.styleSheet()
            layout.addWidget(button, row, col)
            col += 1
            if col > 1: row, col = row + 1, 0
        return group
    
    def create_telemetry_panel(self):
        group = QGroupBox()
        layout = QVBoxLayout(group)
        self.pos_label, self.vel_label, self.vbus_label, self.current_lim_label, self.current_state_label = QLabel(), QLabel(), QLabel(), QLabel(), QLabel()
        for label in [self.pos_label, self.vel_label, self.vbus_label, self.current_lim_label, self.current_state_label]:
            layout.addWidget(label)
        return group
    
    def update_telemetry_labels(self, pos, vel, vbus, current_lim, current_state_id, pos_set, iq_meas, encoder_is_ready, motor_is_calibrated):
        self.last_telemetry_data = (pos, vel, vbus, current_lim, current_state_id, pos_set, iq_meas, encoder_is_ready, motor_is_calibrated)
        state_name = self.AXIS_STATE_MAP.get(current_state_id, f'{self.tr("UNKNOWN")} ({current_state_id})')
        self.pos_label.setText(self.tr("Encoder Position: {0:.2f} °").format(pos * 360.0))
        self.vel_label.setText(self.tr("Estimated Velocity: {0:.2f} [turns/s]").format(vel))
        self.vbus_label.setText(self.tr("Bus Voltage: {0:.2f} [V]").format(vbus))
        self.current_lim_label.setText(self.tr("Current Limit: {0:.2f} [A]").format(current_lim))
        self.current_state_label.setText(self.tr("Current State: {0}").format(state_name))

    def connect_odrive(self):
        if self.odrv_thread is not None:
            self.show_status_message(self.tr("Please wait, connection/disconnection process is in progress."), AppColors.WARNING, 2000)
            return
        if self.connect_button: self.connect_button.setEnabled(False)
        self.show_status_message(self.tr(AppMessages.ODRIVE_SEARCHING), AppColors.WARNING)
        self.status_label.setText(self.tr(AppMessages.STATUS_CONNECTING))
        self.status_label.setStyleSheet(f"color: {AppColors.WARNING}; font-weight: bold;")
        self.odrv_thread = QThread()
        self.odrv_worker = ODriveWorker()
        self.odrv_proxy = self.odrv_worker
        self.odrv_worker.moveToThread(self.odrv_thread)
        self.odrv_thread.started.connect(self.odrv_worker.connect_and_run)
        self.odrv_worker.connection_status.connect(self.handle_connection_status)
        self.odrv_worker.error_detected.connect(self.handle_error_detected)
        self.odrv_worker.telemetry_updated.connect(self.update_telemetry_labels)
        self.odrv_worker.telemetry_updated.connect(self.graph_tab.update_plot)
        self.odrv_worker.telemetry_updated.connect(lambda p,v,vb,cl,cs,ps,im,er,mc: self.encoder_tab.update_calibration_status(er))
        self.odrv_worker.telemetry_updated.connect(lambda p,v,vb,cl,cs,ps,im,er,mc: self.motor_tab.update_motor_calibration_status(mc))
        self.odrv_worker.finished.connect(self.odrv_thread.quit)
        self.odrv_worker.finished.connect(self.odrv_worker.deleteLater)
        self.odrv_thread.finished.connect(self.odrv_thread.deleteLater)
        self.odrv_thread.finished.connect(self.on_thread_finished)
        self.odrv_thread.start()

    def handle_error_detected(self, message):
        self.show_status_message(self.tr("ERROR DETECTED! Click 'Show Errors' for details and to clear."), AppColors.ERROR)
        if self.show_errors_button: 
            self.show_errors_button.setStyleSheet("background-color: #d8b61a; color: black; font-weight: bold;")

    def reset_error_state_ui(self):
        if self.show_errors_button: self.show_errors_button.setStyleSheet(self.original_button_style)
    
    def show_status_message(self, message, color=AppColors.NEUTRAL, timeout=0):
        """Displays a message in the application's status bar with a specified color."""
        self.statusBar().setStyleSheet(f"color: {color};")
        self.statusBar().showMessage(message, timeout)
        
        if timeout > 0:
            QTimer.singleShot(timeout, lambda: self.statusBar().setStyleSheet(self.original_statusbar_style))

    def on_tab_changed(self, index):
        if self.tabs.tabText(index) == self.tr("About"):
            dialog = AboutDialog(self); dialog.exec()
            self.tabs.setCurrentIndex(self.last_tab_index)
        else: self.last_tab_index = index

    def populate_all_fields(self):
        if not self.is_connected: return
        self.show_status_message(self.tr(AppMessages.CONFIG_READING), AppColors.WARNING)
        try:
            for tab in self.config_tabs: tab.populate_fields()
            self.show_status_message(self.tr(AppMessages.CONFIG_READ_SUCCESS), AppColors.SUCCESS, 3000)
        except Exception as e:
            msg = self.tr(AppMessages.CONFIG_READ_ERROR).format(e)
            self.show_status_message(msg, AppColors.ERROR, 5000)
            QMessageBox.critical(self, self.tr("Read Error"), self.tr("Could not read all settings from ODrive.\n\nDetails: {0}").format(e))
            
    def handle_connection_status(self, connected, message):
        self.is_connected = connected
        self.firmware_tab.on_connection_status_changed(connected)
        self.backup_tab.on_connection_status_changed(connected)
        if connected:
            self.status_label.setText(self.tr(AppMessages.STATUS_CONNECTED))
            self.status_label.setStyleSheet(f"color: {AppColors.SUCCESS}; font-weight: bold;")
            self.show_status_message(self.tr(AppMessages.ODRIVE_CONNECTED), AppColors.SUCCESS, 4000)
            QTimer.singleShot(250, self.populate_all_fields)
        else:
            self.status_label.setText(self.tr(AppMessages.STATUS_DISCONNECTED))
            self.status_label.setStyleSheet(f"color: {AppColors.ERROR}; font-weight: bold;")
            self.show_status_message(self.tr("ODrive disconnected: {0}").format(message), AppColors.ERROR)
            self.reset_telemetry_labels(); self.odrv_proxy = None; self.reset_error_state_ui()
            is_normal_disconnect = any(keyword in message.lower() for keyword in ["user", "lost", "disconnected"])
            if not is_normal_disconnect: QMessageBox.critical(self, self.tr("Connection Failed"), message)
        if not connected and self.connect_button: self.connect_button.setEnabled(True)
                
    def reset_telemetry_labels(self):
        self.pos_label.setText(self.tr("Encoder Position: -")); self.vel_label.setText(self.tr("Estimated Velocity: -"))
        self.vbus_label.setText(self.tr("Bus Voltage: -")); self.current_lim_label.setText(self.tr("Current Limit: -"))
        self.current_state_label.setText(self.tr("Current State: -")); self.graph_tab.clear_plot()
        self.last_telemetry_data = None
        
    def disconnect_odrive(self):
        if not self.is_connected or not self.odrv_worker: return
        self.odrv_worker.stop()
        
    def on_thread_finished(self):
        self.odrv_thread, self.odrv_worker = None, None
        if self.is_connected: self.handle_connection_status(False, self.tr(AppMessages.ODRIVE_DISCONNECTED_USER))
        if self.connect_button: self.connect_button.setEnabled(True)
        
    def _execute_odrive_command(self, command_func, success_msg, error_title):
        if not self.is_connected or not self.odrv_proxy:
            self.show_status_message(self.tr(AppMessages.ODRIVE_NOT_CONNECTED_CMD_FAILED), AppColors.ERROR, 3000)
            return False
        try:
            command_func(self.odrv_proxy.odrv)
            if success_msg: self.show_status_message(self.tr(success_msg), AppColors.SUCCESS, 4000)
            return True
        except fibre.protocol.ChannelBrokenException:
            self.show_status_message(self.tr("Command failed: Connection lost."), AppColors.ERROR, 5000); return False
        except Exception as e:
            self.show_status_message(self.tr("Command error: {0}").format(e), AppColors.ERROR, 5000)
            QMessageBox.critical(self, self.tr(error_title), str(e)); return False

    def set_axis0_idle(self): self._execute_odrive_command(lambda odrv: setattr(odrv.axis0, 'requested_state', AppConstants.ODRIVE_EXEC_SCOPE['AXIS_STATE_IDLE']), "Axis 0 set to IDLE state.", "Error setting IDLE state")
    def save_configuration(self): return self._execute_odrive_command(lambda odrv: odrv.save_configuration(), "Configuration saved to ODrive.", "Error Saving Configuration")
    def erase_configuration(self):
        if self._execute_odrive_command(lambda odrv: odrv.erase_configuration(), None, "Error Erasing Configuration"):
            self.show_status_message(self.tr("Configuration erased. Reboot ODrive to apply."), AppColors.WARNING, 5000)

    def reboot_odrive(self):
        if not self.is_connected: QMessageBox.warning(self, self.tr("Warning"), self.tr("ODrive not connected.")); return
        try: self.odrv_proxy.odrv.reboot()
        except Exception: pass
        self.show_status_message(self.tr("Reboot command sent. The ODrive will disconnect."), AppColors.WARNING, 5000)

    def get_errors_as_html(self, odrv):
        with io.StringIO() as buf, redirect_stdout(buf): dump_errors(odrv, True); raw_text = buf.getvalue()
        return f'<pre style="font-family: Consolas, monaco, monospace; font-size: 10pt;">{Ansi2HTMLConverter(dark_bg=True, scheme="xterm").convert(raw_text, full=False)}</pre>'

    def show_errors(self):
        if not self.is_connected: QMessageBox.warning(self, self.tr("Warning"), self.tr("ODrive not connected.")); return
        try:
            odrv = self.odrv_proxy.odrv
            if not (odrv.error or (hasattr(odrv, 'axis0') and odrv.axis0.error) or (hasattr(odrv, 'axis1') and odrv.axis1.error)):
                QMessageBox.information(self, self.tr("Error Status"), self.tr("No errors found on the ODrive.")); return
            dialog = ErrorDialog(self.get_errors_as_html(odrv), self.odrv_proxy, parent=self)
            dialog.errors_cleared.connect(self.on_errors_cleared); dialog.exec()
        except Exception as e: QMessageBox.critical(self, self.tr("Error"), self.tr("Could not read errors from ODrive.\n\nDetails: {0}").format(e))
            
    def on_errors_cleared(self): self.show_status_message(self.tr("Errors cleared."), AppColors.SUCCESS, 3000); self.reset_error_state_ui()

    def show_config(self):
        if not self.is_connected: QMessageBox.warning(self, self.tr("Warning"), self.tr("ODrive not connected.")); return
        try:
            with io.StringIO() as buf, redirect_stdout(buf):
                odrv = self.odrv_proxy.odrv
                print(*["------------- GENERAL ODRIVE CONFIG -------------", odrv.config, "\n\n------------- AXIS 0: GENERAL CONFIG -------------", odrv.axis0.config, "\n\n------------- AXIS 0: MOTOR CONFIG -------------", odrv.axis0.motor.config, "\n\n------------- AXIS 0: ENCODER CONFIG -------------", odrv.axis0.encoder.config, "\n\n------------- AXIS 0: CONTROLLER CONFIG -------------", odrv.axis0.controller.config, "\n\n------------- CAN CONFIG -------------", odrv.can.config], sep='\n')
                ConfigDialog(buf.getvalue(), parent=self).exec()
        except Exception as e: QMessageBox.critical(self, self.tr("Error"), self.tr("Could not read configuration.\n\nDetails: {0}").format(e))
    
    def save_configuration_prompt(self):
        if not self.is_connected or not self.odrv_proxy:
            self.show_status_message(self.tr(AppMessages.ODRIVE_NOT_CONNECTED_CMD_FAILED), AppColors.ERROR, 3000); return
        try:
            if self.odrv_proxy.odrv.axis0.current_state != AppConstants.ODRIVE_EXEC_SCOPE['AXIS_STATE_IDLE']:
                QMessageBox.warning(self, self.tr("Action Required"), self.tr("The motor is not in IDLE state.\n\nTo save the configuration, it must be idle.\n\nClick the 'Set IDLE (Axis 0)' button and try saving again."))
            else: self.save_configuration()
        except Exception as e: QMessageBox.critical(self, self.tr("Error"), self.tr("Could not check motor state or save.\n\nDetails: {0}").format(e))
    
    def erase_configuration_prompt(self):
        if not self.is_connected:
            self.show_status_message(self.tr(AppMessages.ODRIVE_NOT_CONNECTED_CMD_FAILED), AppColors.ERROR, 3000); return
        reply = QMessageBox.warning(self, self.tr('Confirm Destructive Action'), self.tr("<b>WARNING:</b> You are about to erase <b>ALL</b> settings on the ODrive and restore them to factory defaults.<br><br>This action is irreversible and requires a reboot upon completion.<br><br>Do you wish to continue?"), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes: self.erase_configuration()

    def closeEvent(self, event):
        if self.odrv_worker: self.odrv_worker.stop()
        if self.odrv_thread and self.odrv_thread.isRunning():
            self.odrv_thread.quit(); self.odrv_thread.wait(1000)
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    QApplication.setOrganizationName('MarcosSilva')
    QApplication.setApplicationName('ODriveGUIConfigurator')
    settings = QSettings()
    locale = settings.value('language', 'en_US')
    if locale not in ['en_US', 'pt_BR']: locale = 'en_US'
    translator = QTranslator()
    if locale != 'en_US':
        translation_file = resource_path(os.path.join('translations', f'{locale}.qm'))
        if os.path.exists(translation_file) and translator.load(translation_file):
            app.installTranslator(translator)
        else:
            print(f"WARNING: Translation file not found for '{locale}'.")
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyside6'))
    gui = ODriveGUI()
    gui.translator = translator 
    gui.show()
    sys.exit(app.exec())