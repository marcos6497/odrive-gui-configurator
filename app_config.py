# app_config.py

from odrive.enums import *

class AppColors:
    SUCCESS = "lightgreen"
    ERROR = "red"
    WARNING = "orange"
    INFO = "lightblue"
    NEUTRAL = "white"
    STATUS_CALIBRATED_BG = "green" 
    STATUS_NOT_CALIBRATED_BG = "red" 
    STATUS_TEXT = "white"

class AppMessages:
    STATUS_CONNECTING = "Status: Connecting..."
    STATUS_CONNECTED = "Status: Connected"
    STATUS_DISCONNECTED = "Status: Disconnected"
    ODRIVE_SEARCHING = "Searching for ODrive..."
    ODRIVE_FOUND = "ODrive found!"
    ODRIVE_CONNECTED = "ODrive successfully connected."
    ODRIVE_DISCONNECTED_USER = "Disconnected by user"
    ODRIVE_CONNECTION_LOST = "Connection lost"
    ODRIVE_CONNECTION_FAILED = "Could not find an ODrive (timeout)."
    ODRIVE_NOT_CONNECTED_CMD_FAILED = "Command failed: ODrive not connected."
    CONFIG_READING = "Reading ODrive settings..."
    CONFIG_READ_SUCCESS = "Settings read successfully."
    CONFIG_READ_ERROR = "Error reading settings: {}"
    CONFIG_APPLY_SUCCESS = "Settings applied to the current session."
    CONFIG_APPLY_ERROR = "Error applying settings: {}"
    CMD_SUCCESS = "Command '{cmd}' sent successfully."
    CMD_ERROR = "Error executing command: {}"
    SAVE_REMINDER = "To make them permanent, click 'Save Settings' on the main screen."
    CALIBRATING = "Calibrating..."
    CALIBRATION_SUCCESS = "Calibration Completed"
    CALIBRATION_FAILED = "Calibration Failed"

class AppConstants:
    TELEMETRY_INTERVAL_S = 0.1 
    MAX_GRAPH_POINTS = 500    

    ODRIVE_EXEC_SCOPE = {
        'AXIS_STATE_IDLE': AXIS_STATE_IDLE,
        'AXIS_STATE_FULL_CALIBRATION_SEQUENCE': AXIS_STATE_FULL_CALIBRATION_SEQUENCE,
        'AXIS_STATE_ENCODER_INDEX_SEARCH': AXIS_STATE_ENCODER_INDEX_SEARCH,
        'AXIS_STATE_MOTOR_CALIBRATION': AXIS_STATE_MOTOR_CALIBRATION,
        'AXIS_STATE_CLOSED_LOOP_CONTROL': AXIS_STATE_CLOSED_LOOP_CONTROL
    }

    FALLBACK_AXIS_STATE_NAMES = { 
        1: 'IDLE', 
        3: 'FULL_CALIBRATION_SEQUENCE',
        5: 'MOTOR_CALIBRATION',
        6: 'ENCODER_OFFSET_CALIBRATION',
        7: 'ENCODER_INDEX_SEARCH', 
        8: 'CLOSED_LOOP_CONTROL' 
    }