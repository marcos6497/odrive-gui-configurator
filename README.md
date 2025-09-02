# ODrive GUI Configurator

A modern graphical interface for configuring and monitoring ODrive boards, developed in Python and distributed as a compiled `.exe` application.

---

🌍 Languages: [🇧🇷 Português](README-ptbr.md) | [🇺🇸 English](README.md)


## 🚀 Features

### 🔌 Connection and Control
- **Connect to ODrive**: Starts communication and loads the board’s configuration data.  
- **Disconnect from ODrive**: Manually stops communication with the board.  
- **Reboot ODrive**: Sends the reboot command to the board.  
- **Clear Errors**: Clears all error flags on the ODrive.  
- **Erase Configuration**: Restores the ODrive to factory settings.  
- **Set Axis 0 to IDLE**: Puts axis 0 into the IDLE state, required before saving the configuration.  
- **Save Configuration**: Saves the current settings to the ODrive’s non-volatile memory.  
- **Backup and Restore**: Allows backing up and restoring the ODrive configuration.  
- **Firmware Update**: Facilitates updating the ODrive firmware.  
- **DC Power**: Settings and real-time readings of the power supply.  
- **Motor**: Motor configuration, calibration, and real-time status.  
- **Encoder**: Encoder calibration, settings, and real-time status.  
- **CAN**: CAN communication configuration and parameters.  
- **Graph**: Real-time visual monitoring of ODrive parameters.  
- **Terminal**: Direct interaction with ODrive via commands.  

### 📊 Real-Time Monitoring
- Encoder position (in degrees).  
- Estimated velocity (turns/s).  
- Bus voltage (VBus) in volts.  
- Configured current limit (A).  
- Current axis state (`AXIS_STATE_*`).  
- Real-time plot with continuous updates.  

### 🧰 Errors and Diagnostics
- **Show Errors** – Opens a dedicated window that lists all current ODrive errors, highlighted with HTML.  
- **Clear Errors** – A button to reset the board's errors.  

---

### 🌍 Languages
- 🇧🇷 Português (pt-BR) 
- 🇺🇸 English (en-US)

## ⚙️ Screenshots

### ⚡ DC Power Tab

- **Voltage Limits:** Set minimum and maximum DC bus voltage for safe operation.  
- **Current Limits:** Define max positive, negative, and regenerative current.  
- **Brake Resistor:** Enable/disable brake resistor and set its resistance value.  
- **Apply Settings:** Apply the configured power source parameters to ODrive. 
 <img width="852" height="636" alt="{7886C65F-5D60-43C0-98D3-BD28E6C3CFED}" src="https://github.com/user-attachments/assets/17c88a37-335b-45cb-b79a-ba74ce94c8ce" />

### 🔧 Motor Tab

- **Main Settings:** Set pole pairs, torque constant, motor type, and default control mode.  
- **Limits & Control:** Configure max current, bandwidth, and power thresholds. Options to disable velocity limit, torque mode limit, and overspeed error.  
- **Motor Calibration:** Run calibration with adjustable current/voltage and save calibration data.  
<img width="853" height="636" alt="{99D119FD-7554-4DD2-A463-35AF69682090}" src="https://github.com/user-attachments/assets/4d590af7-f1f7-4ab3-979a-e56e1e708bd4" />

### 🎛️ Encoder Tab

- **Basic Settings:** Select encoder mode, set counts per revolution (CPR), bandwidth, and check calibration status.  
- **Startup Method:** Choose no action, calibrate on each startup, or use Z-Index for fast startup. Options to save calibration and search index at startup.  
- **Closed-Loop Control:** Option to enable closed-loop control automatically on startup.  
<img width="852" height="632" alt="{6D1A52DF-8C0B-47C1-9BB1-40A2AEDB84A8}" src="https://github.com/user-attachments/assets/c7644b52-c60e-4bc3-8354-2d29b2464c24" />

### 🛰️ CAN Tab

- **Node ID:** Set the CAN bus node ID for the selected axis.  
- **Baud Rate:** Configure the CAN communication speed.  
- **Apply Settings:** Save and apply CAN bus parameters to ODrive.  
<img width="851" height="631" alt="{560E9DCA-52DE-458F-A188-F6F2B9155B09}" src="https://github.com/user-attachments/assets/91da439e-487b-431b-8b66-6b974ad204a6" />

### 🔄 Firmware Tab

- **Device Info:** Displays firmware version, hardware version, and serial number.  
- **Update Steps:** Enter DFU mode, check DFU status, and reboot when needed.  
- **Prerequisites (Windows):** Requires **STM32CubeProgrammer** installed.  
- **Firmware Flashing:** Select a firmware file and flash it to the ODrive. Progress and messages appear in the flashing log.  

<img width="853" height="634" alt="image" src="https://github.com/user-attachments/assets/1aa8e16f-7b17-4828-a486-c9f5c72a19e7" />

### 📈 Graph Tab

- **Display Plots:** Visualize real-time data such as actual position, target position (setpoint), velocity, and measured current (Iq).  
- **Controls:** Pause or clear the plot for a fresh view.  
- **Usage:** Useful for tuning and analyzing ODrive performance in real time.  
<img width="853" height="633" alt="{7DAC07F1-F0B0-4F86-8BC5-A835024355E3}" src="https://github.com/user-attachments/assets/0a55ef1b-7144-464a-8d79-c704d2ad0442" />

### 🖥️ Terminal Tab

- **Command Input:** Send commands directly to the ODrive.  
- **Output Window:** Displays command history and responses.  
- **Controls:** Options to clear the terminal or access help.  
- **Usage:** Provides full low-level interaction with the ODrive firmware.  
<img width="855" height="633" alt="{579087C6-4BB8-477F-93A4-8CF6E54D76ED}" src="https://github.com/user-attachments/assets/86ae1bee-fe22-4ade-8ac5-19b17dee8948" />

### 💾 Backup Tab

- **Export Configuration:** Save all ODrive settings to a JSON file (reliable and compatible with all firmware versions).  
- **Import Configuration:** Restore settings from a JSON file. ⚠️ This will overwrite all current ODrive settings and cannot be undone.  
- **Process Log:** Displays details of backup and restore operations.  

<img width="852" height="633" alt="{8E27F1A6-D6E3-42B9-9650-7215BABB5855}" src="https://github.com/user-attachments/assets/51c629f0-e31c-493b-8659-c727c894ba8d" />

### 🚨 Show Errors

- **Error Viewer:** Displays all current errors on the ODrive (system, axis, motor, encoder, controller, etc.).  
- **Details:** Lists specific fault codes such as `MOTOR_FAILED`, `DRV_FAULT`, and other diagnostics.  
- **Controls:**  
  - **Clear Errors:** Reset all error flags.  
  - **Close:** Exit the error viewer.  

<img width="852" height="196" alt="{9780564A-CE61-42CB-87F0-CEBBBDB2C4D5}" src="https://github.com/user-attachments/assets/4519d4f4-87ea-4991-afcd-cc3919761d7c" />
<img width="853" height="633" alt="{6CB82502-6BA4-45F6-8E79-EE02BCB0C62E}" src="https://github.com/user-attachments/assets/ec188fde-c88b-445c-8e7d-f1c4fdc652d5" />

---

## ⚙️ Technical Overview

- Built with **Python 3.8+** and **PySide6 (Qt for Python)**.  
- Modular structure: each tab (Motor, Encoder, DC Power, CAN, Firmware, Graph, Terminal, Backup) is in `tabs/`.  
- Main file: `main.py` launches the application.  
- Uses **PyQtGraph** for real-time plots.  
- ODrive communication handled via the official `odrive` Python library.  
- Can be compiled into a `.exe` using **PyInstaller**.  

### 📦 Installation

Clone the repository and install dependencies:

```bash
# 1. Clone the repository
git clone https://github.com/marcos6497/odrive-gui-configurator.git
cd odrive-gui

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the environment (Windows PowerShell)
venv\Scripts\Activate.ps1    

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run app
python main.py

```


## 📦 Download
👉 The compiled `.exe` version is available on the [**Releases**](https://github.com/marcos6497/odrive-gui-configurator/releases) tab.  
Just download and run — no installation required.  

---

## 💖 Support / Donate

If this project helped you, consider supporting its development:

- [💵 PayPal](https://www.paypal.com/donate/?business=HTDDRZL6XCVSE&no_recurring=0&currency_code=BRL)  

---

## 🎥 Video Demonstration (pt-BR)

Watch the full demonstration of **ODrive GUI Configurator** on YouTube:

[![ODrive GUI Configurator - Video](https://img.youtube.com/vi/gNRW3H_NcU8/0.jpg)](https://www.youtube.com/watch?v=gNRW3H_NcU8)

---

## 📄 License
This project uses third-party libraries. See [licenses](LICENSES) for details.
