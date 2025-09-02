# tabs/graph_tab.py
"""
This module defines the GraphTab class, which provides a real-time plotting interface
for visualizing ODrive telemetry data using pyqtgraph.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, QPushButton, QLabel
from PySide6.QtCore import Qt, QEvent
import pyqtgraph as pg
from collections import deque

class GraphTab(QWidget):
    """
    Manages the UI tab for real-time data plotting. It is a standalone QWidget
    and receives telemetry data via its update_plot slot.
    """
    def __init__(self, main_window, parent=None):
        """Initializes the GraphTab, setting up UI, plot curves, and data buffers."""
        super().__init__(parent)
        self.main_window = main_window
        self.is_plotting = True
        self.time_index = 0
        self.max_points = 500

        self.time_data = deque(maxlen=self.max_points)
        self.pos_estimate_data = deque(maxlen=self.max_points)
        self.vel_estimate_data = deque(maxlen=self.max_points)
        self.iq_measured_data = deque(maxlen=self.max_points)
        self.pos_setpoint_data = deque(maxlen=self.max_points)

        self._setup_ui()
        self.retranslate_ui()

    def changeEvent(self, event):
        """Catches language change events to re-translate the UI."""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslate_ui()
        super().changeEvent(event)

    def _setup_ui(self):
        """Constructs the user interface widgets and layouts for this tab."""
        main_layout = QHBoxLayout(self)

        self.controls_group = QGroupBox()
        controls_layout = QVBoxLayout(self.controls_group)
        self.controls_group.setFixedWidth(200)

        self.label_display_plots = QLabel()
        self.cb_pos_estimate = QCheckBox()
        self.cb_pos_estimate.setChecked(True)
        self.cb_pos_setpoint = QCheckBox()
        self.cb_vel_estimate = QCheckBox()
        self.cb_iq_measured = QCheckBox()
        
        self.pause_button = QPushButton()
        self.pause_button.setCheckable(True)
        self.pause_button.clicked.connect(self._toggle_plotting)
        
        self.clear_button = QPushButton()
        self.clear_button.clicked.connect(self.clear_plot)

        controls_layout.addWidget(self.label_display_plots)
        controls_layout.addWidget(self.cb_pos_estimate)
        controls_layout.addWidget(self.cb_pos_setpoint)
        controls_layout.addWidget(self.cb_vel_estimate)
        controls_layout.addWidget(self.cb_iq_measured)
        controls_layout.addStretch()
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.clear_button)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#222222")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend()


        self.pos_estimate_curve = self.plot_widget.plot(pen=pg.mkPen('c', width=2), name=self.tr("Actual Pos. (turns)"))
        self.pos_setpoint_curve = self.plot_widget.plot(pen=pg.mkPen('g', width=2, style=Qt.PenStyle.DashLine), name=self.tr("Target Pos. (turns)"))
        self.vel_estimate_curve = self.plot_widget.plot(pen=pg.mkPen('y', width=2), name=self.tr("Vel. (turns/s)"))
        self.iq_measured_curve = self.plot_widget.plot(pen=pg.mkPen('m', width=2), name=self.tr("Current (A)"))

        main_layout.addWidget(self.plot_widget, 1)
        main_layout.addWidget(self.controls_group)

    def retranslate_ui(self):
        """Updates all translatable texts in this tab."""
        self.controls_group.setTitle(self.tr("Graph Controls"))
        self.label_display_plots.setText(self.tr("Display Plots:"))
        self.cb_pos_estimate.setText(self.tr("Actual Position"))
        self.cb_pos_setpoint.setText(self.tr("Target Position (Setpoint)"))
        self.cb_vel_estimate.setText(self.tr("Velocity"))
        self.cb_iq_measured.setText(self.tr("Measured Current (Iq)"))
        self._toggle_plotting(self.pause_button.isChecked())
        self.clear_button.setText(self.tr("Clear Plot"))
        self.plot_widget.setLabel('bottom', self.tr('Samples (Time)'))
        self.plot_widget.setLabel('left', self.tr('Values'))

    def _toggle_plotting(self, checked):
        """Pauses or resumes the real-time plotting."""
        self.is_plotting = not checked
        button_text = self.tr("Resume") if checked else self.tr("Pause")
        self.pause_button.setText(button_text)
    
    def clear_plot(self):
        """Clears all data from the plot and resets the time index."""
        self.time_index = 0
        self.time_data.clear()
        self.pos_estimate_data.clear()
        self.pos_setpoint_data.clear()
        self.vel_estimate_data.clear()
        self.iq_measured_data.clear()
        self.update_plot(0, 0, 0, 0, 0, 0, 0, False, False)

    def update_plot(self, pos_est, vel_est, vbus, current_lim, current_state, pos_set, iq_meas, encoder_ready, motor_calibrated):
        """
        Slot that receives telemetry data and updates the plot curves accordingly.
        """
        if not self.is_plotting:
            return

        self.time_data.append(self.time_index)
        self.pos_estimate_data.append(pos_est)
        self.pos_setpoint_data.append(pos_set)
        self.vel_estimate_data.append(vel_est)
        self.iq_measured_data.append(iq_meas)
        self.time_index += 1

        if self.cb_pos_estimate.isChecked():
            self.pos_estimate_curve.setData(list(self.time_data), list(self.pos_estimate_data))
        else:
            self.pos_estimate_curve.clear()

        if self.cb_pos_setpoint.isChecked():
            self.pos_setpoint_curve.setData(list(self.time_data), list(self.pos_setpoint_data))
        else:
            self.pos_setpoint_curve.clear()

        if self.cb_vel_estimate.isChecked():
            self.vel_estimate_curve.setData(list(self.time_data), list(self.vel_estimate_data))
        else:
            self.vel_estimate_curve.clear()

        if self.cb_iq_measured.isChecked():
            self.iq_measured_curve.setData(list(self.time_data), list(self.iq_measured_data))
        else:
            self.iq_measured_curve.clear()