# tabs/can_tab.py
"""
This module defines the CANTab class, which provides a user interface for configuring
the CAN bus settings on the ODrive, such as Node ID and Baud Rate.
"""
from PySide6.QtWidgets import (
    QLabel, QLineEdit, QPushButton, QVBoxLayout, QGridLayout, QGroupBox, QComboBox, QMessageBox
)
from PySide6.QtGui import QIntValidator
# --- MUDANÇA: QEvent é necessário para a tradução dinâmica ---
from PySide6.QtCore import Qt, QEvent

from .base_tab import BaseTab
from app_config import AppMessages 

class CANTab(BaseTab):
    """
    Manages the UI tab for CAN bus configuration.
    """
    def __init__(self, main_window, parent=None):
        """Initializes the CANTab, setting up UI and initial state."""
        super().__init__(main_window, parent)
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
        
        # --- UI Widget Creation ---
        self.group = QGroupBox()
        group_layout = QGridLayout(self.group)
        self.label_node_id = QLabel()
        self.can_node_id = QLineEdit()
        self.label_baud_rate = QLabel()
        self.can_baud_rate = QComboBox()
        for rate in ["125000", "250000", "500000", "1000000"]:
            self.can_baud_rate.addItem(rate)
        
        # --- Widget Configuration ---
        int_validator = QIntValidator(0, 127, self)
        self.can_node_id.setValidator(int_validator)
        self.apply_btn = QPushButton()
        self.apply_btn.clicked.connect(self.apply_config)
        
        # --- Layout Assembly ---
        group_layout.addWidget(self.label_node_id, 0, 0)
        group_layout.addWidget(self.can_node_id, 0, 1)
        group_layout.addWidget(self.label_baud_rate, 1, 0)
        group_layout.addWidget(self.can_baud_rate, 1, 1)
        
        main_layout.addWidget(self.group)
        main_layout.addStretch()
        main_layout.addWidget(self.apply_btn, 0, Qt.AlignmentFlag.AlignRight)

    # --- MUDANÇA: Adiciona a nova função retranslate_ui ---
    def retranslate_ui(self):
        """Updates all translatable texts in this tab."""
        self.group.setTitle(self.tr("CAN Bus Settings"))
        self.can_node_id.setToolTip(self.tr("CAN node ID for Axis 0. Usually a number from 0 to 63."))
        self.can_baud_rate.setToolTip(self.tr("Transmission rate for the CAN bus."))
        self.label_node_id.setText(self.tr("Node ID (Axis 0):"))
        self.label_baud_rate.setText(self.tr("Baud Rate:"))
        self.apply_btn.setText(self.tr("Apply CAN Settings"))

    def populate_fields(self):
        """Reads CAN configuration from the connected ODrive and updates the UI fields."""
        odrv = self.get_odrv()
        if not odrv: return
        self.can_node_id.setText(str(odrv.axis0.config.can.node_id))
        self.can_baud_rate.setCurrentText(str(odrv.can.config.baud_rate))

    def apply_config(self):
        """Applies the settings from the UI fields to the connected ODrive."""
        odrv = self.get_odrv()
        if not odrv: return
        try:
            node_id_text = self.can_node_id.text().replace(',', '.')
            odrv.axis0.config.can.node_id = int(node_id_text)
            odrv.can.config.baud_rate = int(self.can_baud_rate.currentText())
            self.main_window.show_status_message(self.tr("CAN settings applied."), "lightgreen", 3000)
            
            reminder_message = f"{self.tr(AppMessages.CONFIG_APPLY_SUCCESS)}.\n\n{self.tr(AppMessages.SAVE_REMINDER)}"
            QMessageBox.information(self, self.tr("Reminder"), reminder_message)
        except ValueError:
            QMessageBox.critical(self, self.tr("Input Error"), self.tr("The Node ID is invalid. Please check that the field is not empty."))
        except Exception as e:
            error_message = self.tr("Error applying CAN config: {}").format(e)
            self.main_window.show_status_message(error_message, "red", 5000)