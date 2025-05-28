import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QProgressBar, QPushButton, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QConicalGradient, QFont
import subprocess
import os
import math

# Batch script filename
BATCH_SCRIPT_NAME = "cleaner.bat"

# Key phrases from cleaner.bat that signify progress stages
# (Using more complete phrases for better matching if output changes slightly)
KEY_PHRASES = [
    "ÕýÔÚÇå³ýϵͳÀ¬»øÎļþ",  # Start of "ÕýÔÚÇå³ýϵͳÀ¬»øÎļþ£¬ÇëÉԵÈ......"
    "Deleting *.tmp files...",
    "Deleting *.log files...",
    "Deleting *.old files...",
    "Çå³ýϵͳLJÍê³ɣ¡"        # Start of "Çå³ýϵͳLJÍê³ɣ¡"
]

class ProcessRunner(QThread):
    new_output = pyqtSignal(str)
    process_finished = pyqtSignal()
    progress_increment = pyqtSignal() 

    def __init__(self, script_path, key_phrases):
        super().__init__()
        self.script_path = script_path
        self.key_phrases = key_phrases
        self.matched_phrases_indices = set() 
        self.process = None

    def run(self):
        if not os.path.exists(self.script_path):
            self.new_output.emit(f"Error: Batch script '{self.script_path}' not found.")
            self.process_finished.emit()
            return
        try:
            self.process = subprocess.Popen(
                [self.script_path],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                shell=True, bufsize=1, 
                creationflags=subprocess.CREATE_NO_WINDOW # Hide console for .bat
            )
            for line in iter(self.process.stdout.readline, b''):
                try:
                    decoded_line = line.decode('gbk').rstrip()
                except UnicodeDecodeError:
                    try:
                        decoded_line = line.decode('cp936').rstrip()
                    except UnicodeDecodeError:
                        # Fallback to utf-8, ignoring errors if other decodings fail
                        decoded_line = line.decode('utf-8', errors='ignore').rstrip()
                
                self.new_output.emit(decoded_line)

                for i, phrase in enumerate(self.key_phrases):
                    if phrase in decoded_line and i not in self.matched_phrases_indices:
                        self.progress_increment.emit()
                        self.matched_phrases_indices.add(i) 
                        break 
            self.process.stdout.close()
            self.process.wait()
        except Exception as e:
            self.new_output.emit(f"Error running script: {str(e)}")
        finally:
            self.process_finished.emit()

class RadarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200) # Min size for the widget
        self.angle = -90  # Initial angle (pointing upwards)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.is_animating = False

        self.pulse_timer = QTimer(self) # Timer for target pulsing effect
        self.pulse_timer.timeout.connect(self.update_pulse)
        self.pulse_alpha_offset = 0 # Current offset for pulsing alpha
        self.pulse_direction = 1  # Direction of pulse alpha change

        # Refined color palette for a "cool" tech look
        self.background_color = QColor(20, 30, 40)  # Dark blue-gray
        self.grid_color = QColor(50, 100, 50, 100)  # Muted green, more transparent
        self.sweep_leading_color = QColor(140, 255, 140, 230) # Bright, slightly transparent leading edge
        self.sweep_trail_color = QColor(80, 220, 80, 180)   # Main body of the sweep
        self.dot_base_color = QColor(180, 255, 180)        # Base color for targets
        self.dot_highlight_color = QColor(230, 255, 230)   # Highlight color when sweep hits target
        self.idle_sweep_color = QColor(70, 150, 70, 120)   # Color for the static line in idle mode

        # Targets: (radius_ratio from center, angle_degrees, base_dot_size, pulse_speed_factor)
        self.targets = [
            (0.3, 45, 5, 1.0), (0.5, 135, 6, 0.8), (0.7, 225, 5, 1.2), 
            (0.4, 310, 6, 0.9), (0.6, 90, 7, 1.0), (0.2, 15, 5, 1.1), 
            (0.8, 180, 6, 0.7), (0.65, 270, 5, 1.3)
        ] 

    def start_animation(self):
        self.is_animating = True
        self.angle = -90 # Ensure sweep starts from top
        self.timer.start(33)  # Target ~30 FPS for smooth animation
        if not self.pulse_timer.isActive():
            self.pulse_timer.start(50) # Start pulsing targets
        self.update()

    def stop_animation(self):
        self.is_animating = False
        self.timer.stop()
        # Keep targets pulsing even in idle state for a "live" feel
        self.angle = -90 # Reset to pointing up
        self.update()

    def update_pulse(self):
        # Creates a subtle oscillation for target alpha/size
        if self.pulse_alpha_offset >= 40: self.pulse_direction = -1 # Max pulse offset
        elif self.pulse_alpha_offset <= -30: self.pulse_direction = 1 # Min pulse offset
        self.pulse_alpha_offset += (1.5 * self.pulse_direction) # Speed of pulse
        
        # If radar is idle, still need to trigger repaint for pulsing targets
        if not self.timer.isActive(): 
            self.update()

    def update_animation(self):
        self.angle = (self.angle + 3.5) % 360  # Speed of radar sweep
        self.update()  # Trigger paintEvent

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        width, height = self.width(), self.height()
        center_x, center_y = width // 2, height // 2
        radius = min(width, height) // 2 - 15 # Padding from widget edge

        if radius <= 5: return # Avoid drawing if widget is too small

        # 1. Draw Background (dark circle)
        painter.setBrush(QBrush(self.background_color))
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

        # 2. Draw Grid Lines (concentric circles and radial lines)
        painter.setPen(QPen(self.grid_color, 1, Qt.DashLine)) # Dashed lines for grid
        for i in range(1, 5): # 4 concentric circles
            current_radius = radius * i // 4
            painter.drawEllipse(center_x - current_radius, center_y - current_radius, current_radius * 2, current_radius * 2)
        for i in range(0, 360, 45): # Radial lines every 45 degrees
            rad_angle = math.radians(i)
            painter.drawLine(center_x, center_y, center_x + int(radius * math.cos(rad_angle)), center_y + int(radius * math.sin(rad_angle)))

        # 3. Draw Targets (dots)
        for r_ratio, tgt_angle_deg, base_size, pulse_factor in self.targets:
            tgt_radius = radius * r_ratio
            actual_tgt_angle_rad = math.radians(tgt_angle_deg)
            tgt_x = center_x + int(tgt_radius * math.cos(actual_tgt_angle_rad))
            tgt_y = center_y + int(tgt_radius * math.sin(actual_tgt_angle_rad))

            # Pulsing effect for size and alpha
            pulse_val = math.sin((self.pulse_alpha_offset * pulse_factor * math.pi / 180.0)) # Sin wave for smooth pulse
            current_size = base_size + (base_size / 3.5 * pulse_val) # Size variation
            base_alpha = 130 + 70 * pulse_val # Alpha variation (130 +/- 70)
            
            final_alpha, dot_color_to_use = base_alpha, self.dot_base_color

            if self.is_animating:
                # Check if sweep is near this target
                angle_diff = abs(self.angle - tgt_angle_deg)
                if angle_diff > 180: angle_diff = 360 - angle_diff # Normalize difference
                
                sweep_activation_angle = 20 # Degrees within which target is "hit"
                if angle_diff < sweep_activation_angle:
                    activation_factor = (sweep_activation_angle - angle_diff) / sweep_activation_angle
                    final_alpha = base_alpha + (255 - base_alpha) * activation_factor # Increase alpha
                    current_size += 2.5 * activation_factor # Grow slightly when hit
                    dot_color_to_use = self.dot_highlight_color # Change color

            final_dot_color = QColor(dot_color_to_use)
            final_dot_color.setAlpha(int(max(0, min(255, final_alpha)))) # Clamp alpha
            
            painter.setBrush(final_dot_color)
            painter.setPen(Qt.NoPen) # No border for dots
            painter.drawEllipse(int(tgt_x - current_size / 2), int(tgt_y - current_size / 2), int(current_size), int(current_size))

        # 4. Draw Radar Sweep or Idle Line
        if self.is_animating:
            painter.setPen(Qt.NoPen)
            # Angle for QConicalGradient: 0 is at 3 o'clock, counter-clockwise. Our self.angle: 0 is 12 o'clock, clockwise.
            gradient_angle = (-self.angle + 90 + 360) % 360 
            sweep_gradient = QConicalGradient(center_x, center_y, gradient_angle)
            sweep_spread_degrees = 75 # Visual width of the sweep
            
            sweep_gradient.setColorAt(0, self.sweep_leading_color) # Brightest part
            sweep_gradient.setColorAt(0.07, self.sweep_trail_color) # Quick fade to trail color
            sweep_gradient.setColorAt(sweep_spread_degrees / 360.0, QColor(0,0,0,0)) # Fade to transparent
            # Ensure rest of the circle is transparent
            sweep_gradient.setColorAt((sweep_spread_degrees / 360.0) + 0.001, QColor(0,0,0,0)) 
            sweep_gradient.setColorAt(1.0, QColor(0,0,0,0))

            painter.setBrush(QBrush(sweep_gradient))
            # Calculate start angle for drawPie (in 1/16th of a degree)
            pie_draw_start_angle_degrees = (-self.angle + 90 - sweep_spread_degrees + 360) % 360
            painter.drawPie(center_x - radius, center_y - radius, radius * 2, radius * 2, int(pie_draw_start_angle_degrees * 16), int(sweep_spread_degrees * 16))
        else: # Idle state: draw a static line
            painter.setPen(QPen(self.idle_sweep_color, 2, Qt.SolidLine))
            idle_angle_rad = math.radians(self.angle) # Use current angle (should be -90)
            painter.drawLine(center_x, center_y, center_x + int(radius * math.cos(idle_angle_rad)), center_y + int(radius * math.sin(idle_angle_rad)))


class SystemCleanerUI(QWidget):
    def __init__(self):
        super().__init__()
        self.process_runner = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("System Cleaner Pro") # Updated title
        self.setGeometry(100, 100, 700, 950) # Larger window size for better look

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.radar_widget = RadarWidget()
        self.radar_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.radar_widget.setMinimumHeight(380) # Increased min height for radar

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True) # Text (percentage) will be styled by QSS

        self.start_button = QPushButton("Start System Cleanup") # More descriptive
        self.start_button.clicked.connect(self.start_cleanup)

        # Add widgets with stretch factors for better resizing
        main_layout.addWidget(self.radar_widget, 2) # Radar takes more space
        main_layout.addWidget(self.console_output, 1) # Console also expands
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.start_button)

        # Refined spacing and margins
        main_layout.setSpacing(18) 
        main_layout.setContentsMargins(25, 25, 25, 25) 

    def start_cleanup(self):
        self.start_button.setEnabled(False)
        self.start_button.setText("Cleaning in Progress...") # Update button text
        self.console_output.clear()
        self.progress_bar.setValue(0) 
        self.radar_widget.start_animation()

        script_dir = os.path.dirname(os.path.abspath(__file__))
        batch_file_path = os.path.join(script_dir, BATCH_SCRIPT_NAME)
        
        self.console_output.append(f"Initiating cleanup process: {batch_file_path}\n")
        
        self.progress_bar.setMaximum(len(KEY_PHRASES))
        # self.progress_bar.setValue(0) # Already set above

        self.process_runner = ProcessRunner(batch_file_path, KEY_PHRASES)
        self.process_runner.new_output.connect(self.append_output)
        self.process_runner.progress_increment.connect(self.update_progress)
        self.process_runner.process_finished.connect(self.cleanup_finished)
        self.process_runner.start()

    def append_output(self, text):
        self.console_output.append(text)
        self.console_output.ensureCursorVisible() # Scroll to bottom

    def update_progress(self):
        current_value = self.progress_bar.value()
        if current_value < self.progress_bar.maximum():
            self.progress_bar.setValue(current_value + 1)

    def cleanup_finished(self):
        self.start_button.setEnabled(True)
        self.start_button.setText("Start System Cleanup")
        self.progress_bar.setValue(self.progress_bar.maximum()) 
        self.console_output.append("\nSystem Cleanup Process Finished.") # Updated message
        self.process_runner = None 
        self.radar_widget.stop_animation()

# Global Dark Theme Stylesheet
DARK_THEME_STYLESHEET = """
QWidget {
    background-color: #282c34; 
    color: #abb2bf; 
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 10pt; /* Base font size */
}

QMainWindow, QDialog { /* Ensure main window and dialogs get the base background */
    background-color: #282c34;
}

QTextEdit {
    background-color: #21252b; /* Slightly darker for console */
    color: #c8ccd4; /* Brighter text for console readability */
    border: 1px solid #3e4451; /* Subtle border */
    border-radius: 4px; 
    padding: 8px;
    font-family: "Consolas", "Menlo", "Courier New", monospace; /* Monospaced font */
    font-size: 9.5pt; /* Slightly smaller for console */
}

QPushButton {
    background-color: #4e5666; /* Button background */
    color: #d0d8e8; /* Button text color */
    border: 1px solid #5c6370;
    border-radius: 5px;
    padding: 10px 15px; /* Generous padding */
    min-height: 22px; /* Minimum button height */
    font-weight: bold;
}

QPushButton:hover {
    background-color: #5a6272; /* Lighter on hover */
    border: 1px solid #67768c;
}

QPushButton:pressed {
    background-color: #434a56; /* Darker when pressed */
}

QPushButton:disabled {
    background-color: #3e4451; /* Style for disabled state */
    color: #7f848e;
}

QProgressBar {
    border: 1px solid #3e4451;
    border-radius: 6px; /* Rounded corners for the bar */
    text-align: center; 
    background-color: #21252b; /* Background of the progress bar itself */
    color: #abb2bf; /* Color of the percentage text */
    font-weight: bold;
    height: 24px; /* Taller progress bar */
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                      stop:0 #61AFEF, stop:0.7 #56C0C8, stop:1 #48D1CC); /* Blue to Teal/Turquoise gradient */
    border-radius: 5px; /* Rounded corners for the chunk, slightly less than parent for inset look */
    /* margin: 0.5px; */ /* Optional: small margin for chunk */
}

QLabel { /* Basic label styling */
    color: #abb2bf;
    background-color: transparent; /* Ensure labels don't have their own background unless specified */
}

RadarWidget { /* Specific for RadarWidget if needed, though it handles its own background */
    background-color: transparent; 
}
"""

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Apply the dark theme stylesheet to the entire application
    app.setStyleSheet(DARK_THEME_STYLESHEET) 
    ex = SystemCleanerUI()
    ex.show()
    sys.exit(app.exec_())
