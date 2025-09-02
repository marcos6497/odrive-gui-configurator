# tabs/base_tab.py

from PySide6.QtWidgets import QWidget
from app_config import AppMessages, AppColors

class BaseTab(QWidget):
    """
    Base class for all configuration tabs.
    Provides common functionalities such as access to the ODrive object and
    a standardized interface for populating and applying settings.
    """
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window

    def get_odrv(self):
        """Convenience method to safely get the ODrive object."""
        if self.main_window.is_connected and self.main_window.odrv_proxy:
            return self.main_window.odrv_proxy.odrv
        
        self.main_window.show_status_message(
            AppMessages.ODRIVE_NOT_CONNECTED_CMD_FAILED, 
            AppColors.ERROR, 
            3000
        )
        return None

    def populate_fields(self):
        """Abstract method that must be implemented by subclasses to load data from the ODrive."""
        raise NotImplementedError("Subclass must implement the 'populate_fields' method.")

    def apply_config(self):
        """Abstract method that must be implemented by subclasses to apply settings to the ODrive."""
        raise NotImplementedError("Subclass must implement the 'apply_config' method.")