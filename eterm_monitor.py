import tkinter as tk
from tkinter import scrolledtext
import os # Added for os.path.exists
import pygetwindow # Added for window interaction
import pyautogui # Added for sending keys and screenshots
import time # Added for potential delays
import mss # For screen capture
import pytesseract # For OCR
from PIL import Image # For image manipulation with mss and pytesseract
import re # For regular expressions used in parsing
import threading # For running the monitoring loop in a separate thread
try:
    import winsound # For playing sound on Windows
    WINDOWS_SOUND_ENABLED = True
except ImportError:
    WINDOWS_SOUND_ENABLED = False
    print("Info: 'winsound' module not found. Sound notifications will be disabled (this is expected on non-Windows systems).")


CONFIG_FILE = "config.txt"

# Configure Tesseract path (NOTE: This path is Windows-specific)
# In a Linux environment (like the sandbox), Tesseract is usually in the PATH if installed.
# If Tesseract is not found, OCR will fail.
try:
    # Try to set the command path, but don't error out if system is not Windows or path is incorrect.
    # The error will be caught later if Tesseract is actually used and not found.
    pytesseract.pytesseract.tesseract_cmd = r'D:\Python\Scripts\tesseract.exe'
except Exception as e:
    print(f"Info: Could not set Tesseract command path (may not be relevant on this system): {e}")

def load_window_title():
    try:
        with open(CONFIG_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def save_window_title(title):
    with open(CONFIG_FILE, "w") as f:
        f.write(title)

# Window Interaction Functions
def get_window_by_title(title_substring):
    """
    Finds a window whose title contains the given substring.
    Returns the first matching window object or None.
    """
    try:
        windows = pygetwindow.getWindowsWithTitle(title_substring)
        if windows:
            if len(windows) > 1:
                print(f"Warning: Multiple windows found with title substring '{title_substring}'. Returning the first one: {windows[0].title}")
            return windows[0]
        else:
            print(f"Info: No window found with title substring '{title_substring}'.")
            return None
    except Exception as e:
        print(f"Error finding window by title '{title_substring}': {e}")
        return None

def send_keys_to_window(window_title_substring, keys_to_send, interval=0.05):
    """
    Finds a window by its title substring, activates it, and sends keys.
    (Existing function - content omitted for brevity in diff, but remains in file)
    """
    print(f"Attempting to send keys to window containing title: '{window_title_substring}'")
    window = get_window_by_title(window_title_substring)

    if window:
        try:
            if window.isMinimized:
                window.restore()
            if not window.isActive:
                window.activate()

            # Allow a brief moment for the window to activate
            time.sleep(0.2)

            print(f"Sending keys '{keys_to_send}' to window '{window.title}'")
            if isinstance(keys_to_send, (list, tuple)):
                pyautogui.hotkey(*keys_to_send)
                print(f"Sent hotkey sequence: {keys_to_send}")
            else:
                pyautogui.typewrite(str(keys_to_send), interval=interval)
                print(f"Typed string: {keys_to_send}")
            return True
        except Exception as e:
            # Attempt to provide more specific error if possible
            if not window.isActive:
                print(f"Error: Window '{window.title}' could not be activated before sending keys.")
            print(f"Error sending keys to window '{window.title}': {e}")
            return False
    else:
        print(f"Failed to send keys: Window with title substring '{window_title_substring}' not found.")
        return False

# Screen Capture and OCR Functions
def capture_screen_region(x, y, width, height):
    """
    Captures a specific region of the screen.
    Returns a PIL Image object or None if capture fails.
    Coordinates are relative to the primary screen.
    """
    print(f"Attempting to capture screen region: x={x}, y={y}, width={width}, height={height}")
    try:
        with mss.mss() as sct:
            monitor = {"top": y, "left": x, "width": width, "height": height}
            sct_img = sct.grab(monitor)
            # Convert to PIL Image
            img = Image.frombytes("RGB", (sct_img.width, sct_img.height), sct_img.rgb, "raw", "RGB")
            print("Screen region captured successfully.")
            return img
    except Exception as e:
        print(f"Error capturing screen region: {e}")
        return None

def ocr_image(image_data, lang='eng'):
    """
    Performs OCR on the given image data (PIL Image object).
    Returns the extracted text or None if OCR fails.
    """
    if image_data is None:
        print("OCR Error: No image data provided.")
        return None

    print(f"Performing OCR with language: {lang}")
    try:
        text = pytesseract.image_to_string(image_data, lang=lang)
        print(f"OCR successful. Extracted text snippet: '{text[:50].strip()}...'")
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        print("OCR Error: Tesseract is not installed or not found in your PATH.")
        print("Please ensure Tesseract is installed and the path is correctly configured if needed.")
        return None
    except Exception as e:
        print(f"Error during OCR: {e}")
        return None

def capture_and_ocr_region(x, y, width, height, lang='eng'):
    """
    Captures a screen region and performs OCR on it.
    Returns the extracted text or None.
    """
    print(f"Starting capture and OCR for region: x={x}, y={y}, w={width}, h={height}, lang={lang}")
    image_obj = capture_screen_region(x, y, width, height)
    if image_obj:
        text = ocr_image(image_obj, lang=lang)
        return text
    else:
        print("Capture and OCR failed because screen capture failed.")
        return None

# Flight Data Parsing and Availability Logic
def extract_flight_segments(ocr_text):
    """
    Parses OCR text to identify segments for each flight.
    Returns a dictionary: {"flight_number": "text_segment"}
    """
    print("Extracting flight segments from OCR text...")
    segments = {}
    if not ocr_text:
        print("Warning: OCR text is empty, cannot extract segments.")
        return segments

    # Regex to find lines starting with a number, then capturing the flight ID (e.g., "1 CA123", "1.CA123", "1MU456")
    # It looks for a digit, optional dot/space, then a 2-char airline code, then 3-5 digits for flight number.
    flight_line_starts = list(re.finditer(r"^\s*\d+\s*[.\s]?\s*([A-Z0-9]{2}\d{3,5})", ocr_text, re.MULTILINE))

    for i, match in enumerate(flight_line_starts):
        flight_number_match = match.group(1) # The captured flight number like CA123
        # Clean flight number (remove non-alphanumeric, e.g. if airline code was part of it by mistake)
        # Assuming flight numbers are typically like "CA1234" or "MU567"
        flight_number_cleaned = re.sub(r'[^A-Z0-9]', '', flight_number_match)
        # Heuristic: if it starts with digits (e.g. from line number "1CA123"), remove leading digits.
        # This is a bit risky if flight numbers can start with digits after airline code.
        # For now, assuming standard format like CA123, not 123CA
        # A better approach might be to ensure it starts with 2 letters.
        if re.match(r"^[A-Z]{2}", flight_number_cleaned):
             # Standard format like CA123
             pass
        elif re.match(r"^\d+[A-Z]{2}", flight_number_cleaned): # e.g. 1CA123 from "1 CA123" where space was missed
             flight_number_cleaned = re.sub(r"^\d+", "", flight_number_cleaned)


        segment_start_pos = match.start()
        # Determine end of segment
        if i + 1 < len(flight_line_starts):
            segment_end_pos = flight_line_starts[i+1].start()
        else:
            segment_end_pos = len(ocr_text)

        flight_text_segment = ocr_text[segment_start_pos:segment_end_pos].strip()

        # The actual flight number used as key should be extracted from the segment's first line carefully
        first_line_of_segment = flight_text_segment.split('\n', 1)[0]
        # More robust extraction of flight number from the first line of the segment
        fn_match_in_segment = re.search(r"([A-Z0-9]{2}\s?\d{3,5}(\s?[A-Z])?)", first_line_of_segment) # Allows optional suffix like CA1234 A
        if fn_match_in_segment:
            key_flight_number = fn_match_in_segment.group(1).replace(" ", "") # e.g. CA1234A
            # Further clean to ensure it's a standard flight ID format, e.g. remove line number prefix if captured
            key_flight_number = re.sub(r"^\d+[.\s]*", "", key_flight_number) # remove "1. " from "1. CA123"

            # Store the segment associated with this key_flight_number.
            # The value is the full text block starting from the line number (e.g., "1 CA123...")
            # We use the first line of the segment as the basis for the value to be stored,
            # not just the "flight_number_cleaned" which might be too aggressive.
            segments[key_flight_number] = flight_text_segment
            print(f"Found segment for {key_flight_number}:\n{flight_text_segment[:100]}...")
        else:
            print(f"Warning: Could not reliably extract flight number key from segment: {first_line_of_segment}")

    if not segments:
        print("No flight segments extracted. Check OCR text format and regex.")
    return segments

def check_cabin_availability(flight_text_segment, cabin_classes_to_check):
    """
    Checks availability for specified cabin classes within a flight's text segment.
    Returns a dictionary: {"cabin_class": "status"}
    Status: "Available", "Unavailable", "Not Configured"
    """
    availability = {}
    print(f"Checking cabin availability for classes: {cabin_classes_to_check} in segment:\n{flight_text_segment[:100]}...")

    for cabin in cabin_classes_to_check:
        # Regex to find cabin class followed by its status indicator.
        # Example: T3, LA, K0, ZC, UL (U is cabin, L is status)
        # Pattern: CabinCode(Status) -> Status can be A, 1-9 (Available) or C,L,U,0,X (Unavailable)
        # We need to be careful about multi-line segments.
        # Replacing newlines with spaces for easier regex matching across lines,
        # though this might be too broad if structure is very rigid.
        normalized_segment = flight_text_segment.replace('\n', ' ')

        # Pattern for the cabin and its status: CabinLetter(StatusLetterOrDigit)
        # e.g. T3, LA, K0, ZC. Using \s? for optional space due to OCR.
        regex_pattern = re.compile(r"{}\s?([A-Z0-9])".format(re.escape(cabin)))
        match = regex_pattern.search(normalized_segment)

        if match:
            status_indicator = match.group(1)
            if status_indicator == 'A' or ('1' <= status_indicator <= '9'):
                availability[cabin] = "Available"
            elif status_indicator == 'C' or status_indicator == 'L' or \
                 status_indicator == 'U' or status_indicator == '0' or \
                 status_indicator == 'X':
                availability[cabin] = "Unavailable"
            else:
                # If status indicator is a letter not in the A,C,L,U,X set, or a digit not 0-9.
                # This case might need refinement based on real data.
                # For now, consider it as not clearly available or unavailable.
                availability[cabin] = f"Unknown status ({status_indicator})"
                print(f"Cabin {cabin}: Unknown status indicator '{status_indicator}'.")

        else:
            availability[cabin] = "Not Configured" # Cabin class not found in the text
            print(f"Cabin {cabin}: Not found in segment.")

    print(f"Cabin availability results: {availability}")
    return availability

def parse_ocr_data(ocr_text, target_flights, target_cabins):
    """
    Main function to parse OCR text for specified flights and cabin classes.
    Returns a dictionary: {"flight_number": {"cabin_class": "status"}}
    """
    print(f"Parsing OCR data for flights: {target_flights}, cabins: {target_cabins}")
    if not ocr_text:
        print("Error: OCR text is empty. Cannot parse.")
        # Return structure indicating no data for all target flights
        results = {}
        for flight_no in target_flights:
            results[flight_no] = {cabin: "OCR Data Missing" for cabin in target_cabins}
        return results

    all_flight_segments = extract_flight_segments(ocr_text)
    parsed_results = {}

    if not all_flight_segments:
        print("Warning: No flight segments were extracted from OCR text.")
        # Populate results with "Flight Not Found" for all target flights
        for flight_no in target_flights:
            parsed_results[flight_no] = {cabin: "Flight Data Not Found in OCR" for cabin in target_cabins}
        return parsed_results

    for flight_no in target_flights:
        # Normalize target_flight_no for matching keys from extract_flight_segments (e.g. remove spaces)
        normalized_target_flight_no = flight_no.replace(" ", "")

        # Find the segment key that matches/contains this flight number.
        # This is needed because segment keys might have suffixes e.g. "CA1501A"
        actual_segment_key = None
        for key in all_flight_segments.keys():
            if normalized_target_flight_no in key: # Simple substring check
                actual_segment_key = key
                break

        if actual_segment_key and actual_segment_key in all_flight_segments:
            print(f"Processing segment for target flight: {flight_no} (using key: {actual_segment_key})")
            segment_text = all_flight_segments[actual_segment_key]
            cabin_status = check_cabin_availability(segment_text, target_cabins)
            parsed_results[flight_no] = cabin_status
        else:
            print(f"Target flight {flight_no} not found in extracted segments.")
            parsed_results[flight_no] = {cabin: "Flight Not Found in OCR" for cabin in target_cabins}

    print(f"Final parsed results: {parsed_results}")
    return parsed_results

class EtermMonitorApp:
    def __init__(self, master):
        self.master = master
    'keys_to_send' can be a string for typing, or a list/tuple for hotkeys.
    Example: send_keys_to_window("Eterm", "AV PEKSHA/+/CA/D")
             send_keys_to_window("Eterm", ['ctrl', 'delete'])
    """
    print(f"Attempting to send keys to window containing title: '{window_title_substring}'")
    window = get_window_by_title(window_title_substring)

    if window:
        try:
            if window.isMinimized:
                window.restore()
            if not window.isActive:
                window.activate()

            # Allow a brief moment for the window to activate
            time.sleep(0.2)

            print(f"Sending keys '{keys_to_send}' to window '{window.title}'")
            if isinstance(keys_to_send, (list, tuple)):
                pyautogui.hotkey(*keys_to_send)
                print(f"Sent hotkey sequence: {keys_to_send}")
            else:
                pyautogui.typewrite(str(keys_to_send), interval=interval)
                print(f"Typed string: {keys_to_send}")
            return True
        except Exception as e:
            # Attempt to provide more specific error if possible
            if not window.isActive:
                print(f"Error: Window '{window.title}' could not be activated before sending keys.")
            print(f"Error sending keys to window '{window.title}': {e}")
            return False
    else:
        print(f"Failed to send keys: Window with title substring '{window_title_substring}' not found.")
        return False

class EtermMonitorApp:
    def __init__(self, master):
        self.master = master
        master.title("Eterm Monitor")

        self.monitoring_active = False
        self.monitoring_thread = None
        # Placeholder - ideally this is set by user interaction
        self.screenshot_region = {'x': 0, 'y': 0, 'width': 800, 'height': 600} # Default values

        # Frame for input fields
        input_frame = tk.Frame(master)
        input_frame.pack(pady=10)

        # Screenshot Region Inputs
        screenshot_frame = tk.LabelFrame(input_frame, text="Screenshot Region")
        screenshot_frame.grid(row=0, column=0, columnspan=2, pady=5, padx=5, sticky="ew")

        tk.Label(screenshot_frame, text="X:").grid(row=0, column=0, sticky="w")
        self.region_x_var = tk.StringVar(value=str(self.screenshot_region['x']))
        self.region_x_entry = tk.Entry(screenshot_frame, textvariable=self.region_x_var, width=7)
        self.region_x_entry.grid(row=0, column=1, padx=2)

        tk.Label(screenshot_frame, text="Y:").grid(row=0, column=2, sticky="w")
        self.region_y_var = tk.StringVar(value=str(self.screenshot_region['y']))
        self.region_y_entry = tk.Entry(screenshot_frame, textvariable=self.region_y_var, width=7)
        self.region_y_entry.grid(row=0, column=3, padx=2)

        tk.Label(screenshot_frame, text="Width:").grid(row=1, column=0, sticky="w")
        self.region_w_var = tk.StringVar(value=str(self.screenshot_region['width']))
        self.region_w_entry = tk.Entry(screenshot_frame, textvariable=self.region_w_var, width=7)
        self.region_w_entry.grid(row=1, column=1, padx=2)

        tk.Label(screenshot_frame, text="Height:").grid(row=1, column=2, sticky="w")
        self.region_h_var = tk.StringVar(value=str(self.screenshot_region['height']))
        self.region_h_entry = tk.Entry(screenshot_frame, textvariable=self.region_h_var, width=7)
        self.region_h_entry.grid(row=1, column=3, padx=2)

        self.focus_x_button = tk.Button(screenshot_frame, text="Set Region (Focus X)", command=lambda: self.region_x_entry.focus_set())
        self.focus_x_button.grid(row=0, column=4, rowspan=2, padx=5, pady=2, sticky="ns")


        # Window Title
        tk.Label(input_frame, text="Window Title:").grid(row=1, column=0, sticky="w", pady=(10,0))
        self.window_title_var = tk.StringVar(value=load_window_title())
        self.window_title_entry = tk.Entry(input_frame, textvariable=self.window_title_var, width=30)
        self.window_title_entry.grid(row=1, column=1, pady=(10,2), sticky="w")
        # Save on focus out
        self.window_title_entry.bind("<FocusOut>", lambda event: save_window_title(self.window_title_var.get()))
        tk.Label(input_frame, text="(e.g., Eterm, last input saved)").grid(row=2, column=1, sticky="w", padx=5)

        # Cabin Classes to Monitor
        tk.Label(input_frame, text="Cabin Classes to Monitor:").grid(row=3, column=0, sticky="w")
        self.cabin_classes_entry = tk.Entry(input_frame, width=30)
        self.cabin_classes_entry.grid(row=3, column=1, pady=2, sticky="w")
        tk.Label(input_frame, text="(e.g., T,L,U)").grid(row=4, column=1, sticky="w", padx=5)

        # Flights to Monitor
        tk.Label(input_frame, text="Flights to Monitor:").grid(row=5, column=0, sticky="w")
        self.flights_entry = tk.Entry(input_frame, width=30)
        self.flights_entry.grid(row=5, column=1, pady=2, sticky="w")
        tk.Label(input_frame, text="(e.g., CA1507,CA1501)").grid(row=6, column=1, sticky="w", padx=5)

        # Clear Screen Command
        tk.Label(input_frame, text="Clear Screen Command:").grid(row=7, column=0, sticky="w")
        self.clear_command_entry = tk.Entry(input_frame, width=30)
        self.clear_command_entry.insert(0, "Ctrl+Delete") # Default value
        self.clear_command_entry.grid(row=7, column=1, pady=2, sticky="w")
        tk.Label(input_frame, text="(default: Ctrl+Delete)").grid(row=8, column=1, sticky="w", padx=5)

        # Flight Query Command
        tk.Label(input_frame, text="Flight Query Command:").grid(row=9, column=0, sticky="w")
        self.query_command_entry = tk.Entry(input_frame, width=30)
        self.query_command_entry.insert(0, "AV PEKSHA/+/CA/D") # Default value
        self.query_command_entry.grid(row=9, column=1, pady=2, sticky="w")
        tk.Label(input_frame, text="(e.g., AV PEKSHA/+/CA/D)").grid(row=10, column=1, sticky="w", padx=5)

        # Monitoring Frequency
        tk.Label(input_frame, text="Monitoring Frequency (seconds):").grid(row=11, column=0, sticky="w")
        self.frequency_entry = tk.Entry(input_frame, width=30)
        self.frequency_entry.insert(0, "10") # Default value
        self.frequency_entry.grid(row=11, column=1, pady=2, sticky="w")

        # Frame for action buttons
        action_frame = tk.Frame(master)
        action_frame.pack(pady=5)

        self.start_button = tk.Button(action_frame, text="Start Monitoring", command=self.start_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(action_frame, text="Stop Monitoring", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Frame for console output
        console_frame = tk.Frame(master)
        console_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        tk.Label(console_frame, text="Console Output:").pack(anchor="w")
        self.console_output = scrolledtext.ScrolledText(console_frame, height=10, width=70)
        self.console_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        self.console_output.configure(state='disabled') # Make it read-only initially

        self.clear_console_button = tk.Button(console_frame, text="Clear Console", command=self._clear_console)
        self.clear_console_button.pack(pady=5)

    def _clear_console(self):
        self.console_output.configure(state='normal')
        self.console_output.delete("1.0", tk.END)
        self.console_output.configure(state='disabled')

    def log_message(self, message):
        """ Safely logs a message to the GUI console from any thread. """
        def _update_console():
            is_empty = self.console_output.index('end-1c') == "1.0"
            self.console_output.configure(state='normal')

            # Prepend message, ensuring it's at the very top (1.0)
            current_content = self.console_output.get("1.0", tk.END)
            self.console_output.delete("1.0", tk.END)
            self.console_output.insert("1.0", message + "\n")
            if current_content.strip(): # Add previous content back if any
                self.console_output.insert(tk.END, current_content)

            self.console_output.see("1.0") # Scroll to the top to see the new message
            self.console_output.configure(state='disabled')

        if self.master.winfo_exists(): # Check if window still exists
            self.master.after_idle(_update_console)
        else:
            print(f"Debug (log_message): Window closed, message: {message}")


    def _parse_key_command_string(self, command_str):
        """ Parses a command string like "Ctrl+Delete" into ['ctrl', 'delete'] or "text" """
        command_str = command_str.strip()
        if not command_str:
            return None
        if '+' in command_str: # Likely a hotkey combination
            return [key.strip().lower() for key in command_str.split('+')]
        elif len(command_str) > 1 and command_str.lower() in pyautogui.KEYBOARD_KEYS: # single special key
             return [command_str.lower()]
        else: # Assume it's text to type
            return command_str

    def _monitoring_thread_function(self):
        self.log_message("Monitoring thread started.")

        # Retrieve static GUI inputs once (or they could be dynamic if GUI allows changes during monitoring)
        try:
            eterm_window_title = self.window_title_var.get()
            raw_clear_cmd = self.clear_command_entry.get()
            flight_query_cmd = self.query_command_entry.get() # This is likely text to type

            monitored_flights_str = self.flights_entry.get()
            monitored_cabins_str = self.cabin_classes_entry.get()
            frequency_sec = int(self.frequency_entry.get())

            if not eterm_window_title:
                self.log_message("Error: Eterm Window Title is not set.")
                self.stop_monitoring() # Request stop
                return # Exit thread

            parsed_clear_cmd = self._parse_key_command_string(raw_clear_cmd)
            if not parsed_clear_cmd:
                 self.log_message(f"Warning: Clear screen command is empty or invalid: '{raw_clear_cmd}'")


            target_flights = [f.strip().upper() for f in monitored_flights_str.split(',') if f.strip()]
            target_cabins = [c.strip().upper() for c in monitored_cabins_str.split(',') if c.strip()]

            if not target_flights:
                self.log_message("Error: No flights to monitor specified.")
                self.stop_monitoring()
                return
            if not target_cabins:
                self.log_message("Error: No cabin classes to monitor specified.")
                self.stop_monitoring()
                return
            if frequency_sec <= 0:
                self.log_message("Error: Monitoring frequency must be positive.")
                self.stop_monitoring()
                return
        except ValueError:
            self.log_message("Error: Invalid monitoring frequency. Please enter a number.")
            self.stop_monitoring()
            return
        except Exception as e:
            self.log_message(f"Error retrieving GUI inputs: {e}")
            self.stop_monitoring()
            return


        while self.monitoring_active:
            cycle_start_time = time.time()
            self.log_message("Starting new monitoring cycle...")

            # 1. Clear Screen
            if parsed_clear_cmd:
                if send_keys_to_window(eterm_window_title, parsed_clear_cmd):
                    self.log_message(f"Sent clear screen command: {raw_clear_cmd}")
                else:
                    self.log_message(f"Failed to send clear screen command to '{eterm_window_title}'. OCR might be inaccurate.")
                time.sleep(0.5) # Delay for window to react
            else:
                self.log_message("Skipping clear screen command as it's not configured.")


            # 2. Send Flight Query
            if flight_query_cmd:
                if send_keys_to_window(eterm_window_title, flight_query_cmd): # Assuming typewrite for this
                    self.log_message(f"Sent flight query command: {flight_query_cmd}")
                else:
                    self.log_message(f"Failed to send flight query command to '{eterm_window_title}'.")
                    # If query fails, maybe wait and retry or stop? For now, continue to OCR.
                time.sleep(1.5) # Delay for Eterm to update
            else:
                self.log_message("Flight query command is empty. Cannot proceed with query.")
                # Potentially skip OCR if query is essential
                # For now, we'll let it try to OCR whatever is there.

            # 3. Capture and OCR
            if not self.screenshot_region or \
               any(k not in self.screenshot_region for k in ['x', 'y', 'width', 'height']):
                self.log_message("Error: Screenshot region is not properly configured.")
                self.stop_monitoring() # Critical error
                break

            ocr_text = capture_and_ocr_region(
                self.screenshot_region['x'], self.screenshot_region['y'],
                self.screenshot_region['width'], self.screenshot_region['height']
            )

            if ocr_text:
                self.log_message(f"Captured and OCR'd. Text (first 100 chars): '{ocr_text[:100].strip() elliptic_text_end '...' if len(ocr_text) > 100 else ''}'")
                # 4. Parse Data
                parsed_data = parse_ocr_data(ocr_text, target_flights, target_cabins)
                self.log_message(f"Parsed data: {parsed_data}")
                # --- Notification Logic Integration ---
                for flight_no, cabins in parsed_data.items():
                    for cabin_code, status in cabins.items():
                        if status == "Available":
                            msg = f"Flight {flight_no} Cabin {cabin_code}: AVAILABLE!"
                            self.log_message(f"NOTIFICATION: {msg}")
                            # Schedule GUI updates on the main thread
                            self.master.after_idle(self.show_notification_popup, msg, "lightgreen")
                            self.play_notification_sound() # Sound can be played directly from thread
                        elif status == "Unavailable":
                            # Optional: notify for unavailable or just log it.
                            msg = f"Flight {flight_no} Cabin {cabin_code}: Unavailable."
                            self.log_message(f"NOTIFICATION (Info): {msg}")
                            self.master.after_idle(self.show_notification_popup, msg, "lightgrey") # lightcoral changed to lightgrey
                            # No sound for unavailable
                        elif status == "Not Configured":
                            msg = f"Flight {flight_no} Cabin {cabin_code}: Not Configured in OCR."
                            self.log_message(f"NOTIFICATION (Info): {msg}")
                            self.master.after_idle(self.show_notification_popup, msg, "lightgrey")
                            # No sound for not configured
                        elif "Unknown status" in status: # Handle unknown status from check_cabin_availability
                            msg = f"Flight {flight_no} Cabin {cabin_code}: {status}."
                            self.log_message(f"NOTIFICATION (Warning): {msg}")
                            self.master.after_idle(self.show_notification_popup, msg, "lightyellow")
                            # No sound for unknown status
                # --- End Notification Logic ---
            else:
                self.log_message("OCR failed or returned no text.")

            # 5. Wait for next cycle
            elapsed_time = time.time() - cycle_start_time
            wait_time = frequency_sec - elapsed_time
            if wait_time > 0:
                self.log_message(f"Waiting for {wait_time:.2f} seconds...")
                # Check monitoring_active flag periodically during wait for responsiveness
                for _ in range(int(wait_time * 10)): # Check every 0.1s
                    if not self.monitoring_active:
                        break
                    time.sleep(0.1)
                if not self.monitoring_active: # Check again if loop broke early
                     self.log_message("Monitoring stopped during wait period.")
                     break
            else:
                self.log_message("Warning: Monitoring cycle took longer than frequency interval.")

            if not self.monitoring_active:
                 self.log_message("Monitoring stopping as requested after cycle completion.")
                 break

        # Loop finished
        self.log_message("Monitoring thread stopped.")
        # Ensure GUI updates are done on the main thread
        self.master.after_idle(lambda: {
            self.start_button.config(state=tk.NORMAL),
            self.stop_button.config(state=tk.DISABLED)
        })

    def start_monitoring(self):
        if self.monitoring_active:
            self.log_message("Monitoring is already active.")
            return

        self.log_message("Validating inputs for monitoring start...")

        # Update and validate screenshot_region from GUI entries
        try:
            new_x = int(self.region_x_var.get())
            new_y = int(self.region_y_var.get())
            new_w = int(self.region_w_var.get())
            new_h = int(self.region_h_var.get())
            if new_w <= 0 or new_h <= 0:
                self.log_message("Error: Screenshot region width and height must be positive.")
                return
            self.screenshot_region = {'x': new_x, 'y': new_y, 'width': new_w, 'height': new_h}
            self.log_message(f"Screenshot region updated to: {self.screenshot_region}")
        except ValueError:
            self.log_message("Error: Screenshot region X, Y, Width, Height must be valid integers.")
            return

        # Validate frequency
        try:
            freq = int(self.frequency_entry.get())
            if freq <= 0:
                self.log_message("Error: Monitoring frequency must be a positive number.")
                return
        except ValueError:
            self.log_message("Error: Monitoring frequency is not a valid number.")
            return

        # Validate other essential fields
        if not self.window_title_var.get():
            self.log_message("Error: Window Title cannot be empty.")
            return
        if not self.flights_entry.get():
            self.log_message("Error: Flights to Monitor cannot be empty.")
            return
        if not self.cabin_classes_entry.get():
            self.log_message("Error: Cabin Classes to Monitor cannot be empty.")
            return


        self.monitoring_active = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.log_message("Starting monitoring...")

        # Create and start the monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_thread_function, daemon=True)
        self.monitoring_thread.start()

    def stop_monitoring(self):
        if not self.monitoring_active:
            self.log_message("Monitoring is not currently active.")
            return

        self.log_message("Requesting monitoring to stop...")
        self.monitoring_active = False
        # The thread will observe this flag and stop.
        # Button states will be updated by the thread when it exits.
        # If thread is stuck, it might not update. Consider a timeout for join if needed.
        # For now, this relies on the thread checking monitoring_active periodically.

    def play_notification_sound(self):
        if WINDOWS_SOUND_ENABLED:
            try:
                winsound.PlaySound("SystemNotification", winsound.SND_ALIAS | winsound.SND_ASYNC)
                self.log_message("Played notification sound.")
            except Exception as e:
                self.log_message(f"Error playing sound: {e}")
        else:
            self.log_message("Skipping sound notification (winsound not available).")

    def show_notification_popup(self, message, color):
        """Shows a Toplevel notification pop-up."""
        if not self.master.winfo_exists(): # Ensure main window is still around
            self.log_message(f"Main window closed, cannot show popup: {message}")
            return

        popup = tk.Toplevel(self.master)
        popup.wm_overrideredirect(True) # Borderless
        popup.configure(bg=color, padx=10, pady=10)

        # Simple label for the message
        label = tk.Label(popup, text=message, bg=color, font=("Arial", 12))
        label.pack()

        # Calculate position (e.g., top right corner of the main window or screen)
        # For simplicity, let's try to position it near the top-right of the screen initially.
        # More sophisticated positioning might require knowing screen dimensions.
        self.master.update_idletasks() # Ensure master window dimensions are current
        master_x = self.master.winfo_x()
        master_y = self.master.winfo_y()
        master_width = self.master.winfo_width()

        # Estimate popup width based on message length (very rough)
        popup_width = len(message) * 8 + 40 # Rough estimate
        popup_height = 50 # Rough estimate

        # Position at top-right of the master window for now
        # x_pos = master_x + master_width - popup_width - 10 # 10px offset
        # y_pos = master_y + 10 # 10px offset

        # Let's try screen's top right. Requires getting screen dimensions.
        # pyautogui can do this, but let's avoid adding dependency here if not already used for this.
        # For now, a simpler fixed offset from master or just centered on master.

        # Center on master window
        # First, get popup's actual requested width/height
        popup.update_idletasks()
        req_width = popup.winfo_reqwidth()
        req_height = popup.winfo_reqheight()

        x_pos = master_x + (master_width // 2) - (req_width // 2)
        y_pos = master_y + (self.master.winfo_height() // 2) - (req_height // 2)

        # Simplified positioning: top-right-ish of where the app might be
        # This is very basic and might not be ideal on all systems/screen setups
        # Try to get screen width, otherwise fallback if master isn't fully realized.
        try:
            screen_width = self.master.winfo_screenwidth()
            x_offset = screen_width - req_width - 20 # 20px from right edge
            y_offset = 20 # 20px from top edge
        except tk.TclError: # Can happen if window not fully managed yet
            x_offset = master_x + master_width - req_width - 20
            y_offset = master_y + 20


        # Ensure it's not off-screen in a weird way if screenwidth is small (e.g. headless)
        x_pos = max(0, x_offset)
        y_pos = max(0, y_offset)

        popup.geometry(f"{req_width}x{req_height}+{x_pos}+{y_pos}") # Set size explicitly too

        self.log_message(f"Showing notification: '{message}' at ({x_pos},{y_pos})")
        self.master.after(5000, popup.destroy) # Auto-close after 5 seconds


if __name__ == "__main__":
    root = tk.Tk()
    app = EtermMonitorApp(root)

    # Ensure config.txt is created with a default/loaded title on first startup
    window_title_to_save = app.window_title_var.get()
    if not window_title_to_save and not os.path.exists(CONFIG_FILE):
        window_title_to_save = "Eterm" # Default title if nothing loaded and file doesn't exist
        app.window_title_var.set(window_title_to_save)
    save_window_title(window_title_to_save) # Save the determined title

    root.mainloop()
