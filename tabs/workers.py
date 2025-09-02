# tabs/workers.py
"""
This module contains worker classes designed to run tasks in separate threads,
preventing the main GUI from freezing. It includes workers for ODrive communication,
motor calibration, and encoder calibration.
"""
import time
from PySide6.QtCore import QObject, Signal, QCoreApplication
import fibre
import odrive
from odrive.enums import (
    AXIS_STATE_IDLE,
    AXIS_STATE_MOTOR_CALIBRATION,
    AXIS_STATE_ENCODER_INDEX_SEARCH,
    AXIS_STATE_ENCODER_OFFSET_CALIBRATION
)

from app_config import AppMessages, AppConstants

class ODriveWorker(QObject):
    """
    Main worker that manages continuous communication with the ODrive.
    Runs in a separate thread to avoid freezing the GUI.
    """
    connection_status = Signal(bool, str)
    telemetry_updated = Signal(float, float, float, float, int, float, float, bool, bool)
    error_detected = Signal(str)
    finished = Signal()

    def __init__(self):
        super().__init__()
        self.odrv = None
        self._is_running = True

    def connect_and_run(self):
        """
        Tries to find and connect to an ODrive. If successful, enters a loop
        to collect telemetry until instructed to stop.
        """
        try:
            print(AppMessages.ODRIVE_SEARCHING) # Console message, not for UI translation
            self.odrv = odrive.find_any(timeout=10)
            print(AppMessages.ODRIVE_FOUND) # Console message
            self.connection_status.emit(True, AppMessages.STATUS_CONNECTED)
            
            while self._is_running:
                try:
                    axis = self.odrv.axis0
                    if axis.error != 0:
                        self.error_detected.emit(f"ERROR: {hex(axis.error)}")
                    
                    self.telemetry_updated.emit(
                        axis.encoder.pos_estimate, axis.encoder.vel_estimate, self.odrv.vbus_voltage, 
                        axis.motor.config.current_lim, axis.current_state, axis.controller.input_pos, 
                        axis.motor.current_control.Iq_measured, axis.encoder.is_ready, axis.motor.is_calibrated
                    )
                except fibre.protocol.ChannelBrokenException:
                    self.connection_status.emit(False, AppMessages.ODRIVE_CONNECTION_LOST)
                    self._is_running = False 
                except Exception as e:
                    # Generic error during runtime
                    error_msg = QCoreApplication.translate("ODriveWorker", "Unexpected worker error: {}").format(e)
                    self.connection_status.emit(False, error_msg)
                    self._is_running = False 
                
                time.sleep(AppConstants.TELEMETRY_INTERVAL_S)

        except TimeoutError:
            self.connection_status.emit(False, AppMessages.ODRIVE_CONNECTION_FAILED)
        except Exception as e:
            # Error during initial connection
            error_msg = QCoreApplication.translate("ODriveWorker", "An error occurred during connection: {}").format(e)
            self.connection_status.emit(False, error_msg)
        
        finally:
            print("Worker finishing and cleaning up resources...") # Console message
            if self.odrv:
                self.odrv = None
            self.finished.emit()
            print("Worker resources cleaned up.") # Console message

    def stop(self):
        """Signals the main loop to stop safely."""
        self._is_running = False

class BaseStateWorker(QObject):
    """
    Base worker for tasks that involve changing the ODrive's state and waiting
    for completion. Encapsulates the state-waiting loop logic with a timeout.
    """
    finished = Signal()
    progress = Signal(str)
    result = Signal(bool, str)

    def __init__(self, odrv):
        super().__init__()
        self.odrv = odrv
        self._is_running = True

    def stop(self):
        self._is_running = False

    def _wait_for_state(self, requested_state, timeout, progress_msg):
        """
        Helper that activates a state and waits for it to complete or time out.
        Returns (True, None) on success, or (False, error_message) on failure.
        """
        if progress_msg:
            self.progress.emit(progress_msg)
        
        # Clear previous errors before starting the operation
        self.odrv.axis0.error = 0
        self.odrv.axis0.motor.error = 0
        self.odrv.axis0.encoder.error = 0

        self.odrv.axis0.requested_state = requested_state
        time.sleep(0.2) # Allow state machine to engage
        
        start_time = time.time()
        while self.odrv.axis0.current_state == requested_state:
            if not self._is_running:
                return False, QCoreApplication.translate("BaseStateWorker", "Operation canceled by user.")
            if time.time() - start_time > timeout:
                self.odrv.axis0.requested_state = AXIS_STATE_IDLE
                timeout_msg = QCoreApplication.translate("BaseStateWorker", "The operation timed out after {} seconds.").format(timeout)
                return False, timeout_msg
            time.sleep(0.1)
        
        if self.odrv.axis0.error != 0:
            error_msg = QCoreApplication.translate("BaseStateWorker", "Error detected on Axis 0: {}").format(hex(self.odrv.axis0.error))
            return False, error_msg

        return True, None 

class MotorCalibrationWorker(BaseStateWorker):
    """Worker specific to performing motor calibration."""
    def run(self):
        """Executes the motor calibration sequence."""
        success, error_msg = self._wait_for_state(
            requested_state=AXIS_STATE_MOTOR_CALIBRATION,
            timeout=25,
            progress_msg=QCoreApplication.translate("MotorCalibrationWorker", "Calibrating Motor...")
        )
        
        if not success:
            self.result.emit(False, error_msg)
            self.finished.emit()
            return
            
        time.sleep(0.5) # Allow values to stabilize

        resistance = self.odrv.axis0.motor.config.phase_resistance
        inductance = self.odrv.axis0.motor.config.phase_inductance
        is_calibrated = self.odrv.axis0.motor.is_calibrated
        motor_error = self.odrv.axis0.motor.error

        if is_calibrated:
            msg = (QCoreApplication.translate("MotorCalibrationWorker", "Motor calibrated successfully!\n\n") +
                   f"{QCoreApplication.translate('MotorCalibrationWorker', 'Phase Resistance')}: {resistance:.4f} Ω\n" +
                   f"{QCoreApplication.translate('MotorCalibrationWorker', 'Phase Inductance')}: {inductance * 1e6:.2f} µH")
            self.result.emit(True, msg)
        else:
            msg = (QCoreApplication.translate("MotorCalibrationWorker", "Motor calibration failed!\n\n") +
                   f"{QCoreApplication.translate('MotorCalibrationWorker', 'Motor Error')}: {hex(motor_error)}\n" +
                   QCoreApplication.translate("MotorCalibrationWorker", "Check calibration current and connections."))
            self.result.emit(False, msg)
        self.finished.emit()

class EncoderCalibrationWorker(BaseStateWorker):
    """Worker specific to encoder calibration (with or without index search)."""
    def __init__(self, odrv, use_index_search):
        super().__init__(odrv)
        self.use_index_search = use_index_search

    def run(self):
        """Executes the appropriate encoder calibration sequence."""
        if self.use_index_search:
            success, error_msg = self._wait_for_state(
                requested_state=AXIS_STATE_ENCODER_INDEX_SEARCH,
                timeout=15,
                progress_msg=QCoreApplication.translate("EncoderCalibrationWorker", "Searching for Index (Z)...")
            )
            if not success:
                self.result.emit(False, error_msg or QCoreApplication.translate("EncoderCalibrationWorker", "Failed to find index."))
                self.finished.emit()
                return

        success, error_msg = self._wait_for_state(
            requested_state=AXIS_STATE_ENCODER_OFFSET_CALIBRATION,
            timeout=25,
            progress_msg=QCoreApplication.translate("EncoderCalibrationWorker", "Calibrating Offset...")
        )

        if not success:
            self.result.emit(False, error_msg or QCoreApplication.translate("EncoderCalibrationWorker", "Offset calibration failed."))
            self.finished.emit()
            return
            
        time.sleep(0.5) # Allow values to stabilize

        is_ready = self.odrv.axis0.encoder.is_ready
        encoder_error = self.odrv.axis0.encoder.error

        if is_ready:
            msg = QCoreApplication.translate("EncoderCalibrationWorker", "Offset calibration completed successfully!")
            if self.use_index_search:
                msg = QCoreApplication.translate("EncoderCalibrationWorker", "Calibration with index completed successfully!")
            self.result.emit(True, msg)
        else:
            msg = (QCoreApplication.translate("EncoderCalibrationWorker", "Encoder calibration failed.\n\n") +
                   f"{QCoreApplication.translate('EncoderCalibrationWorker', 'Encoder Error')}: {hex(encoder_error)}\n" +
                   QCoreApplication.translate("EncoderCalibrationWorker", "Check connections and settings."))
            self.result.emit(False, msg)
        self.finished.emit()