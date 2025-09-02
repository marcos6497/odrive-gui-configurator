# tabs/terminal_tab.py
"""
This module provides a terminal interface for direct interaction with a connected ODrive.
It includes a QLineEdit with command history and a QTextEdit for displaying outputs.
"""
import io
from contextlib import redirect_stdout, redirect_stderr
import odrive.utils
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QLineEdit, QHBoxLayout, QPushButton, QDialog, QLabel
)
from PySide6.QtGui import QFont, QColor, QPalette
# --- MUDANÇA: QEvent é necessário para a tradução dinâmica ---
from PySide6.QtCore import Qt, QEvent
from odrive.enums import *
from app_config import AppColors, AppMessages

class HistoryLineEdit(QLineEdit):
    """
    A custom QLineEdit that maintains a command history, accessible via the Up and Down arrow keys.
    """
    def __init__(self, parent=None):
        """Initializes the command history."""
        super().__init__(parent)
        self.command_history = []
        self.history_index = 0

    def add_to_history(self, command):
        """Adds a new command to the history if it's not a duplicate of the last one."""
        if command and (not self.command_history or self.command_history[-1] != command):
            self.command_history.append(command)
        self.history_index = len(self.command_history)

    def keyPressEvent(self, event):
        """Handles key presses to navigate through the command history."""
        key = event.key()
        if key == Qt.Key.Key_Up:
            if self.command_history and self.history_index > 0:
                self.history_index -= 1
                self.setText(self.command_history[self.history_index])
            event.accept()
        elif key == Qt.Key.Key_Down:
            if self.command_history and self.history_index < len(self.command_history):
                if self.history_index == len(self.command_history) - 1:
                    self.history_index += 1
                    self.clear()
                else:
                    self.history_index += 1
                    self.setText(self.command_history[self.history_index])
            event.accept()
        else:
            super().keyPressEvent(event)

class TerminalTab(QWidget):
    """
    Manages the UI tab for the terminal, handling command input, execution, and output display.
    """
    def __init__(self, main_window, parent=None):
        """Initializes the TerminalTab and sets up its UI components."""
        super().__init__(parent)
        self.main_window = main_window
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
        """Constructs the user interface for the terminal tab."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setFont(QFont("Consolas", 10))
        palette = self.terminal_output.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor("#1e1e1e"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#cccccc"))
        self.terminal_output.setPalette(palette)

        input_layout = QHBoxLayout()
        self.terminal_input = HistoryLineEdit(self)
        self.terminal_input.setFont(QFont("Consolas", 10))
        self.terminal_input.returnPressed.connect(self.send_command)

        self.help_button = QPushButton()
        self.help_button.clicked.connect(self.show_command_help)
        
        self.clear_button = QPushButton()
        self.clear_button.clicked.connect(self.terminal_output.clear)
        
        input_layout.addWidget(self.terminal_input)
        input_layout.addWidget(self.help_button)
        input_layout.addWidget(self.clear_button)

        layout.addWidget(self.terminal_output, 1)
        layout.addLayout(input_layout)

    # --- MUDANÇA: Adiciona a nova função retranslate_ui ---
    def retranslate_ui(self):
        """Updates all translatable texts in this tab."""
        self.terminal_output.setPlaceholderText(self.tr("Command history and outputs will appear here."))
        self.terminal_input.setPlaceholderText(self.tr("Type a command and press Enter..."))
        self.help_button.setText(self.tr("Help"))
        self.help_button.setToolTip(self.tr("Opens a link to the official ODrive documentation."))
        self.clear_button.setText(self.tr("Clear"))

    def append_output(self, text, color=None):
        """Adds text to the terminal display with an optional color."""
        cursor = self.terminal_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.terminal_output.setTextCursor(cursor)
        if color:
            self.terminal_output.setTextColor(QColor(color))
        self.terminal_output.insertPlainText(text + '\n')
        self.terminal_output.setTextColor(QColor("#cccccc")) 
        self.terminal_output.ensureCursorVisible()

    def send_command(self):
        """Executes the command typed by the user in the ODrive's scope."""
        if not self.main_window.is_connected or not self.main_window.odrv_proxy:
            error_msg = self.tr("! Error: {}").format(AppMessages.ODRIVE_NOT_CONNECTED_CMD_FAILED)
            self.append_output(error_msg, AppColors.ERROR)
            return
            
        command = self.terminal_input.text().strip()
        if not command: return
            
        self.terminal_input.add_to_history(command)
        self.append_output(f">>> {command}", AppColors.SUCCESS)
        self.terminal_input.clear()

        # Define the execution scope for the command
        scope = {
            'odrv': self.main_window.odrv_proxy.odrv,
            'dev0': self.main_window.odrv_proxy.odrv,
            'dump_errors': odrive.utils.dump_errors,
            **{k: v for k, v in globals().items() if k.startswith(('AXIS_STATE_', 'CONTROL_MODE_', 'ENCODER_MODE_', 'MOTOR_TYPE_'))}
        }
        
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        # Redirect stdout and stderr to capture the command's output
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            try:
                result = eval(command, scope)
                if result is not None:
                    print(repr(result))
            except Exception:
                try:
                    exec(command, scope)
                except Exception as e:
                    print(self.tr("Execution Error: {}").format(e))

        stdout_val = stdout_capture.getvalue().strip()
        if stdout_val: self.append_output(stdout_val)
        
        stderr_val = stderr_capture.getvalue().strip()
        if stderr_val:
            error_msg = self.tr("! Error Output: {}").format(stderr_val)
            self.append_output(error_msg, AppColors.WARNING)

    def show_command_help(self):
        """Shows a simple help dialog with a link to the official documentation."""
        dialog = CommandHelpDialog(self)
        dialog.exec()

class CommandHelpDialog(QDialog):
    """A simple dialog providing help information and a link to the ODrive documentation."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 150)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.link_label = QLabel('<a href="https://docs.odriverobotics.com/v/latest/getting-started.html">Official ODrive Documentation</a>')
        self.link_label.setOpenExternalLinks(True)
        self.link_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.close_button = QPushButton()
        self.close_button.clicked.connect(self.accept)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        button_layout.addStretch()
        layout.addWidget(self.info_label)
        layout.addWidget(self.link_label)
        layout.addStretch()
        layout.addLayout(button_layout)
        # --- MUDANÇA: Chama a re-tradução na inicialização ---
        self.retranslate_ui()

    # --- MUDANÇA: Adiciona o método changeEvent ---
    def changeEvent(self, event):
        """Catches language change events to re-translate the UI."""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslate_ui()
        super().changeEvent(event)
        
    # --- MUDANÇA: Adiciona a nova função retranslate_ui ---
    def retranslate_ui(self):
        self.setWindowTitle(self.tr("Terminal Help"))
        self.info_label.setText(self.tr("This terminal allows you to run Python commands directly on the ODrive.<br><br>For the complete list of commands and parameters, please refer to the official documentation:"))
        self.close_button.setText(self.tr("Close"))