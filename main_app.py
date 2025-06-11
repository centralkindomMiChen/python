import tkinter as tk
import tkinter as tk # Ensure tk is imported for tk.Text, tk.Scrollbar, tk.Toplevel
from tkinter import ttk
from tkinter import messagebox, filedialog, Toplevel, Text, Scrollbar # Added filedialog, Toplevel, Text, Scrollbar
from datetime import datetime, timedelta, date
from custom_calendar import CustomCalendar

try:
    import openpyxl
    excel_export_possible_global = True
except ImportError:
    excel_export_possible_global = False
    print("INFO: openpyxl library not found. Excel export will be disabled.")


# Assuming database_handler.py is in the same directory or accessible in PYTHONPATH
from database_handler import (
    connect_db,
    get_records_for_month,
    get_cancelled_records_for_month,
    add_leave_record,
    add_meeting_record,
    get_recent_records,
    update_record_status,
    get_all_records # Import new function
)

# --- Flag to use placeholder data ---
# Set this to True to bypass database connection and use hardcoded dates for highlighting.
# This is useful for UI development/testing when DB is not available or for demonstration.
USE_PLACEHOLDER_DATA = True
# In a real application, this might be False or determined by configuration.

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Leave and Meeting Management")
        self.geometry("1024x768")

        # Attempt "Sapphire Blue" like background
        self.configure(bg="#0F52BA") # A deep blue color

        # Initialize current date for the left calendar
        self._current_left_cal_date = datetime.now() # This is a datetime object
        self.selected_date = None # This will store a datetime.date object

        # Create main frames
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Adjusted height for status bar, subtract status bar height from main frame area
        main_content_height = 768 * 0.9

        self.left_frame = ttk.Frame(self.main_frame, width=1024 * 2/3, height=main_content_height)
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        # Add border to visualize
        self.left_frame.config(borderwidth=2, relief="sunken")

        # --- Dual Calendar Area in Left Frame ---
        self._setup_dual_calendar_area()

        self.right_frame = ttk.Frame(self.main_frame, width=1024 * 1/3, height=main_content_height)
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        # Add border to visualize
        self.right_frame.config(borderwidth=2, relief="sunken")

        # Status bar frame should be packed against the bottom of the root window
        self.status_bar_frame = ttk.Frame(self, height=768 * 0.1)
        self.status_bar_frame.pack(fill=tk.X, side=tk.BOTTOM)
        # Add border to visualize
        self.status_bar_frame.config(borderwidth=2, relief="sunken")

        # Configure grid weights for resizing for the main_frame
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=2) # 2/3 width
        self.main_frame.grid_columnconfigure(1, weight=1) # 1/3 width

        # --- Details Input Area in Left Frame (below calendars) ---
        self.details_input_frame = ttk.LabelFrame(self.left_frame, text="Details for Selected Date", padding=(10, 5))
        self.details_input_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True, side=tk.BOTTOM)
        # Initial prompt in the details input frame
        self._show_initial_prompt_in_details_frame()

        # --- Right Pane: Recent Records Display ---
        self._setup_recent_records_display()

        # Status Bar Labels
        ttk.Label(self.status_bar_frame, text="System Time | CPU: --% | Mem: --% | Net: -- Kbps | Debug Console").pack(side=tk.LEFT, padx=10)

        # Initial population of recent records
        self._update_recent_records_display()

        # Setup status bar content (like export button)
        self._setup_status_bar_content()

    def _setup_status_bar_content(self):
        # Clear existing (like the placeholder label)
        for widget in self.status_bar_frame.winfo_children():
            widget.destroy()

        # Example: Add a dynamic status label (can be updated later)
        self.status_label = ttk.Label(self.status_bar_frame, text="Ready.")
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Add Export Button
        self.export_button = ttk.Button(self.status_bar_frame, text="Export All Data", command=self._export_data_action)
        self.export_button.pack(side=tk.RIGHT, padx=10)

        # Assign the global flag to an instance variable if preferred, or use global directly
        self.excel_export_possible = excel_export_possible_global


    def _setup_dual_calendar_area(self):
        calendar_area_container = ttk.Frame(self.left_frame)
        calendar_area_container.pack(pady=10, padx=5, fill=tk.X, anchor="n")

        # Shared Navigation Frame
        nav_frame = ttk.Frame(calendar_area_container)
        nav_frame.pack(pady=5)

        ttk.Button(nav_frame, text="<< Year", command=self._nav_prev_year, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text="< Month", command=self._nav_prev_month, width=8).pack(side=tk.LEFT, padx=2)
        self.current_month_display = ttk.Label(nav_frame, text="", font=("Arial", 12, "bold"), width=18, anchor="center")
        self.current_month_display.pack(side=tk.LEFT, padx=5) # To display current navigated month/year
        ttk.Button(nav_frame, text="Month >", command=self._nav_next_month, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text="Year >>", command=self._nav_next_year, width=8).pack(side=tk.LEFT, padx=2)

        # Frame to hold the two calendars side-by-side
        calendars_frame = ttk.Frame(calendar_area_container)
        calendars_frame.pack(fill=tk.X, expand=True)

        self.cal1 = CustomCalendar(calendars_frame)
        self.cal1.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)

        self.cal2 = CustomCalendar(calendars_frame)
        self.cal2.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)

        self._update_calendars() # Initial setup

    def _update_calendars(self):
        # Update left calendar
        self.cal1.set_date(self._current_left_cal_date.year, self._current_left_cal_date.month)
        self.current_month_display.config(text=f"{self._current_left_cal_date.strftime('%B %Y')}")


        # Update right calendar to be the month after the left one
        right_cal_date = self._current_left_cal_date.replace(day=1) + timedelta(days=32) # Ensure we are in the next month
        right_cal_date = right_cal_date.replace(day=1) # Go to the first day of that next month
        self.cal2.set_date(right_cal_date.year, right_cal_date.month)

        # --- Fetch and apply highlight data ---
        db_conn = None
        if not USE_PLACEHOLDER_DATA:
            db_conn = connect_db() # Try to connect to the database

        # Data for Calendar 1 (left)
        cal1_year = self._current_left_cal_date.year
        cal1_month = self._current_left_cal_date.month
        cal1_active_records = {'leave_dates': set(), 'meeting_dates': set()}
        cal1_cancelled_records = set()

        if db_conn:
            cal1_active_records = get_records_for_month(db_conn, cal1_year, cal1_month)
            cal1_cancelled_records = get_cancelled_records_for_month(db_conn, cal1_year, cal1_month)
            print(f"DB: Cal1 ({cal1_year}-{cal1_month}) Active: {cal1_active_records}, Cancelled: {cal1_cancelled_records}")
        elif USE_PLACEHOLDER_DATA:
            print(f"PLA: Using placeholder data for Cal1 ({cal1_year}-{cal1_month})")
            if cal1_month == date.today().month and cal1_year == date.today().year: # Example for current month
                cal1_active_records['leave_dates'] = {date(cal1_year, cal1_month, 5), date(cal1_year, cal1_month, 15)}
                cal1_active_records['meeting_dates'] = {date(cal1_year, cal1_month, 10), date(cal1_year, cal1_month, 15)} # Day 15 is both
                cal1_cancelled_records = {date(cal1_year, cal1_month, 20)}

        self.cal1.set_highlight_dates(
            leave_dates=cal1_active_records['leave_dates'],
            meeting_dates=cal1_active_records['meeting_dates'],
            cancelled_dates=cal1_cancelled_records
        )
        self.cal1.draw_calendar() # Redraw to apply highlights

        # Data for Calendar 2 (right)
        cal2_year = right_cal_date.year
        cal2_month = right_cal_date.month
        cal2_active_records = {'leave_dates': set(), 'meeting_dates': set()}
        cal2_cancelled_records = set()

        if db_conn:
            cal2_active_records = get_records_for_month(db_conn, cal2_year, cal2_month)
            cal2_cancelled_records = get_cancelled_records_for_month(db_conn, cal2_year, cal2_month)
            print(f"DB: Cal2 ({cal2_year}-{cal2_month}) Active: {cal2_active_records}, Cancelled: {cal2_cancelled_records}")
        elif USE_PLACEHOLDER_DATA:
            print(f"PLA: Using placeholder data for Cal2 ({cal2_year}-{cal2_month})")
            # Example: Add some placeholder data for the next month if it's August 2024 (for testing)
            if cal2_month == 8 and cal2_year == 2024:
                 cal2_active_records['meeting_dates'] = {date(cal2_year, cal2_month, 3), date(cal2_year, cal2_month, 25)}
                 cal2_cancelled_records = {date(cal2_year, cal2_month, 12)}


        self.cal2.set_highlight_dates(
            leave_dates=cal2_active_records['leave_dates'],
            meeting_dates=cal2_active_records['meeting_dates'],
            cancelled_dates=cal2_cancelled_records
        )
        self.cal2.draw_calendar() # Redraw to apply highlights

        if db_conn:
            db_conn.close()
            print("Database connection closed.")


        # Set callbacks for date selection
        self.cal1.on_date_select_callback = self._handle_date_selection
        self.cal2.on_date_select_callback = self._handle_date_selection


    def _clear_details_input_frame(self):
        for widget in self.details_input_frame.winfo_children():
            widget.destroy()

    def _show_initial_prompt_in_details_frame(self):
        self._clear_details_input_frame()
        self.details_input_frame.config(text="Details for Selected Date") # Reset title
        prompt_label = ttk.Label(self.details_input_frame, text="Click a date on a calendar to add or view entries.", style="Italic.TLabel")
        prompt_label.pack(padx=10, pady=20, anchor="center")
        # You might need to define "Italic.TLabel" style if it doesn't exist
        try:
            self.style.configure("Italic.TLabel", font=("Arial", 10, "italic"))
        except tk.TclError: # In case style attribute doesn't exist on self yet or other issues
             pass # Silently fail on style for prompt, not critical


    def _handle_date_selection(self, selected_date_obj: date):
        self.selected_date = selected_date_obj
        self._clear_details_input_frame()
        self.details_input_frame.config(text=f"Details for {self.selected_date.strftime('%d %B %Y')}")

        # For now, directly show "Add Leave" and "Add Meeting"
        # Later, this area would first check if there's existing data for the date.

        button_frame = ttk.Frame(self.details_input_frame)
        button_frame.pack(pady=10, fill=tk.X) # Fill X to allow centering/distribution

        ttk.Button(button_frame, text="Add Leave", command=self._show_leave_input_form).pack(side=tk.LEFT, padx=5, expand=True)
        ttk.Button(button_frame, text="Add Meeting", command=self._show_meeting_input_form).pack(side=tk.LEFT, padx=5, expand=True)
        ttk.Button(button_frame, text="Delete Entry", command=self._prompt_delete_entry).pack(side=tk.LEFT, padx=5, expand=True)
        # Add a "View Entries" button later if needed

    def _prompt_delete_entry(self):
        if not self.selected_date:
            messagebox.showwarning("No Date Selected", "Please select a date to delete entries from.")
            return

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to mark all entries for {self.selected_date.strftime('%d %B %Y')} as cancelled?\n"
            "This action cannot be directly undone through the UI (though data remains 'cancelled' in DB)."
        )
        if confirm:
            self._delete_entry_action()

    def _delete_entry_action(self):
        if not self.selected_date: # Should be caught by _prompt_delete_entry, but double check
            return

        if USE_PLACEHOLDER_DATA:
            print(f"Simulate Delete (Cancel) for {self.selected_date}")
            # This is where placeholder data manipulation would happen.
            # For simplicity in this step, we'll assume _update_calendars will clear active
            # and show them as cancelled if we had a more sophisticated placeholder system.
            # For now, it mostly tests the UI flow.
            messagebox.showinfo("Success (Simulated)", f"Entries for {self.selected_date} marked as cancelled.")

            # To simulate effect on highlights, clear active and add to cancelled for this date
            # This is a simplified placeholder update logic.
            # In _update_calendars, placeholder data is re-created each time, so this won't persist unless
            # the placeholder generation logic in _update_calendars is made aware of these cancellations.
            # For the purpose of this subtask, showing the message and refreshing is the key part.
            # A proper placeholder system would need its own 'database'.

        else: # Actual DB operation
            db_conn = None
            try:
                db_conn = connect_db()
                if not db_conn:
                    messagebox.showerror("Database Error", "Failed to connect to the database.")
                    return

                # Attempt to cancel leave and meeting for the selected date
                # The update_record_status function returns True on successful SQL execution,
                # even if no rows were updated (e.g., no active record found).
                leave_cancelled_ok = update_record_status(db_conn, 'leave_records', self.selected_date, 'cancelled')
                meeting_cancelled_ok = update_record_status(db_conn, 'meeting_records', self.selected_date, 'cancelled')

                if leave_cancelled_ok and meeting_cancelled_ok:
                    messagebox.showinfo("Success", f"Any active entries for {self.selected_date} have been marked as cancelled.")
                else:
                    # This message might be shown if there was a DB error during one of the updates
                    messagebox.showwarning("Partial Success/Error", "Attempted to cancel entries. Some operations might have failed. Please check logs.")

            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred during deletion: {e}")
            finally:
                if db_conn:
                    db_conn.close()

        # Refresh UI elements
        self._update_calendars()
        self._update_recent_records_display()
        self._cancel_action_show_initial_options_or_clear()


    def _show_leave_input_form(self):
        if not self.selected_date:
            self._show_initial_prompt_in_details_frame()
            return

        self._clear_details_input_frame()
        self.details_input_frame.config(text=f"Add Leave for {self.selected_date.strftime('%d %B %Y')}")

        form_frame = ttk.Frame(self.details_input_frame)
        form_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        ttk.Label(form_frame, text="Leave Type:").grid(row=0, column=0, padx=2, pady=5, sticky="w")
        leave_types = ["Annual Leave", "Parent-Teacher Conference", "Time Off in Lieu", "Other"]
        self.leave_type_combo = ttk.Combobox(form_frame, values=leave_types, state="readonly", width=30)
        self.leave_type_combo.grid(row=0, column=1, padx=2, pady=5, sticky="ew")
        self.leave_type_combo.bind("<<ComboboxSelected>>", self._on_leave_type_change)

        ttk.Label(form_frame, text="Notes:").grid(row=1, column=0, padx=2, pady=5, sticky="nw")
        self.leave_notes_text = tk.Text(form_frame, height=4, width=40, state='disabled', relief="solid", borderwidth=1)
        self.leave_notes_text.grid(row=1, column=1, padx=2, pady=5, sticky="ew")

        form_frame.grid_columnconfigure(1, weight=1) # Make Combobox and Text expand

        button_bar = ttk.Frame(form_frame)
        button_bar.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")

        ttk.Button(button_bar, text="Save Leave", command=self._save_leave_action).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_bar, text="Cancel", command=self._cancel_action_show_initial_options_or_clear).pack(side=tk.RIGHT, padx=5)


    def _on_leave_type_change(self, event=None):
        if self.leave_type_combo.get() == "Other":
            self.leave_notes_text.config(state='normal')
        else:
            self.leave_notes_text.config(state='disabled')
            self.leave_notes_text.delete("1.0", tk.END)

    def _show_meeting_input_form(self):
        if not self.selected_date:
            self._show_initial_prompt_in_details_frame()
            return

        self._clear_details_input_frame()
        self.details_input_frame.config(text=f"Add Meeting for {self.selected_date.strftime('%d %B %Y')}")

        form_frame = ttk.Frame(self.details_input_frame)
        form_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        ttk.Label(form_frame, text="Meeting Content:").grid(row=0, column=0, padx=2, pady=5, sticky="nw")
        self.meeting_content_text = tk.Text(form_frame, height=5, width=40, relief="solid", borderwidth=1)
        self.meeting_content_text.grid(row=0, column=1, padx=2, pady=5, sticky="ew")

        form_frame.grid_columnconfigure(1, weight=1) # Make Text expand

        button_bar = ttk.Frame(form_frame)
        button_bar.grid(row=1, column=0, columnspan=2, pady=10, sticky="ew")

        ttk.Button(button_bar, text="Save Meeting", command=self._save_meeting_action).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_bar, text="Cancel", command=self._cancel_action_show_initial_options_or_clear).pack(side=tk.RIGHT, padx=5)


    def _save_leave_action(self):
        if not self.selected_date:
            messagebox.showwarning("No Date Selected", "Please select a date first.")
            return

        leave_type = self.leave_type_combo.get()
        notes = self.leave_notes_text.get("1.0", tk.END).strip()

        if not leave_type:
            messagebox.showwarning("Validation Error", "Please select a leave type.")
            return
        if leave_type == "Other" and not notes:
            messagebox.showwarning("Validation Error", "Notes are required for 'Other' leave type.")
            return

        if USE_PLACEHOLDER_DATA:
            print(f"Simulate Save Leave for {self.selected_date}: Type='{leave_type}', Notes='{notes}'")
            # Add to placeholder data for immediate feedback if desired
            # This part is tricky as placeholder data isn't designed to be persistent like a DB
            # For now, just print and refresh.
            messagebox.showinfo("Success (Simulated)", "Leave record would be saved.")
            self._update_calendars() # Refresh to show potential (simulated) new highlight
            self._cancel_action_show_initial_options_or_clear()
            return

        db_conn = None
        try:
            db_conn = connect_db()
            if not db_conn:
                messagebox.showerror("Database Error", "Failed to connect to the database.")
                return

            success = add_leave_record(db_conn, self.selected_date, leave_type, notes)

            if success:
                messagebox.showinfo("Success", "Leave record saved successfully.")
                self._update_calendars()
                self._update_recent_records_display() # Refresh recent records
                self._cancel_action_show_initial_options_or_clear()
            else:
                messagebox.showerror("Save Error", "Failed to save leave record.\nThe date might already have an active entry, or a database error occurred.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        finally:
            if db_conn:
                db_conn.close()


    def _save_meeting_action(self):
        if not self.selected_date:
            messagebox.showwarning("No Date Selected", "Please select a date first.")
            return

        content = self.meeting_content_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Validation Error", "Meeting content cannot be empty.")
            return

        if USE_PLACEHOLDER_DATA:
            print(f"Simulate Save Meeting for {self.selected_date}: Content='{content}'")
            messagebox.showinfo("Success (Simulated)", "Meeting record would be saved.")
            self._update_calendars()
            self._update_recent_records_display() # Refresh recent records
            self._cancel_action_show_initial_options_or_clear()
            return

        db_conn = None
        try:
            db_conn = connect_db()
            if not db_conn:
                messagebox.showerror("Database Error", "Failed to connect to the database.")
                return

            success = add_meeting_record(db_conn, self.selected_date, content)
            if success:
                messagebox.showinfo("Success", "Meeting record saved successfully.")
                self._update_calendars()
                self._update_recent_records_display() # Refresh recent records
                self._cancel_action_show_initial_options_or_clear()
            else:
                messagebox.showerror("Save Error", "Failed to save meeting record.\nThe date might already have an active entry, or a database error occurred.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        finally:
            if db_conn:
                db_conn.close()

    def _cancel_action_show_initial_options_or_clear(self):
        if self.selected_date:
            # Re-show the "Add Leave" / "Add Meeting" buttons for the current selected_date
            self._handle_date_selection(self.selected_date)
        else:
            # No date is active, show the initial prompt
            self._show_initial_prompt_in_details_frame()


    def _on_cal1_date_selected(self, date_obj: date): # Type hint
        # This method is now an alias or could be removed if direct _handle_date_selection is used.
        self._handle_date_selection(date_obj)

    def _on_cal2_date_selected(self, date_obj: date): # Type hint
        # This method is now an alias or could be removed if direct _handle_date_selection is used.
        self._handle_date_selection(date_obj)

    def _adjust_month(self, month_delta):

    # def _on_cal2_date_selected(self, date_obj):
    #     print(f"Calendar 2 selected: {date_obj}")

    def _adjust_month(self, month_delta):
        # Calculate new month and year
        current_month = self._current_left_cal_date.month
        current_year = self._current_left_cal_date.year

        new_month_abs = current_year * 12 + current_month -1 + month_delta # 0-indexed absolute month

        new_year = new_month_abs // 12
        new_month = new_month_abs % 12 + 1

        self._current_left_cal_date = self._current_left_cal_date.replace(year=new_year, month=new_month, day=1)
        self._update_calendars()

    def _nav_prev_month(self):
        self._adjust_month(-1)

    def _nav_next_month(self):
        self._adjust_month(1)

    def _nav_prev_year(self):
        self._current_left_cal_date = self._current_left_cal_date.replace(year=self._current_left_cal_date.year - 1, day=1)
        self._update_calendars()

    def _nav_next_year(self):
        self._current_left_cal_date = self._current_left_cal_date.replace(year=self._current_left_cal_date.year + 1, day=1)
        self._update_calendars()

    def _setup_recent_records_display(self):
        # Clear existing placeholder labels from right_frame if any
        for widget in self.right_frame.winfo_children():
            widget.destroy()

        # Recent Leave Display
        self.recent_leave_frame = ttk.LabelFrame(self.right_frame, text="Recent Leave (Last Year)", padding=(5,5))
        self.recent_leave_frame.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)

        leave_cols = {"date": "Date", "type": "Type", "notes": "Notes"}
        self.recent_leave_tree = ttk.Treeview(
            self.recent_leave_frame,
            columns=list(leave_cols.keys()),
            show="headings",
            height=6 # Show fewer rows initially
        )
        for col_id, col_text in leave_cols.items():
            self.recent_leave_tree.heading(col_id, text=col_text)
            if col_id == "date":
                self.recent_leave_tree.column(col_id, width=80, minwidth=70, anchor=tk.W)
            elif col_id == "type":
                self.recent_leave_tree.column(col_id, width=120, minwidth=100, anchor=tk.W)
            else: # notes
                self.recent_leave_tree.column(col_id, width=150, minwidth=100, anchor=tk.W)

        leave_scrollbar = ttk.Scrollbar(self.recent_leave_frame, orient=tk.VERTICAL, command=self.recent_leave_tree.yview)
        self.recent_leave_tree.configure(yscrollcommand=leave_scrollbar.set)

        self.recent_leave_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        leave_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Recent Meetings Display
        self.recent_meetings_frame = ttk.LabelFrame(self.right_frame, text="Recent Meetings (Last Year)", padding=(5,5))
        self.recent_meetings_frame.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)

        meeting_cols = {"date": "Date", "details": "Details"}
        self.recent_meetings_tree = ttk.Treeview(
            self.recent_meetings_frame,
            columns=list(meeting_cols.keys()),
            show="headings",
            height=6
        )
        for col_id, col_text in meeting_cols.items():
            self.recent_meetings_tree.heading(col_id, text=col_text)
            if col_id == "date":
                self.recent_meetings_tree.column(col_id, width=80, minwidth=70, anchor=tk.W)
            else: # details
                self.recent_meetings_tree.column(col_id, width=270, minwidth=150, anchor=tk.W)

        meeting_scrollbar = ttk.Scrollbar(self.recent_meetings_frame, orient=tk.VERTICAL, command=self.recent_meetings_tree.yview)
        self.recent_meetings_tree.configure(yscrollcommand=meeting_scrollbar.set)

        self.recent_meetings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        meeting_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)


    def _populate_treeview(self, treeview_widget, data, column_map):
        # Clear existing items
        for item in treeview_widget.get_children():
            treeview_widget.delete(item)

        # Insert new data
        for record_dict in data:
            # Ensure all keys in column_map are present in record_dict, format if necessary
            values_to_insert = []
            for tree_col_id in column_map.keys(): # Iterate in the order of treeview columns
                data_key = column_map[tree_col_id]
                value = record_dict.get(data_key, "") # Get value or empty string if key missing
                if isinstance(value, date):
                    values_to_insert.append(value.strftime("%Y-%m-%d"))
                else:
                    values_to_insert.append(str(value))
            treeview_widget.insert("", tk.END, values=values_to_insert)


    def _update_recent_records_display(self):
        leave_data = []
        meeting_data = []

        if USE_PLACEHOLDER_DATA:
            print("PLA: Using placeholder data for recent records display.")
            # Create more descriptive placeholder data
            leave_data = [
                {'leave_date': date.today() - timedelta(days=1), 'leave_type': 'Annual Leave', 'notes': 'Quick break'},
                {'leave_date': date.today() - timedelta(days=10), 'leave_type': 'Time Off in Lieu', 'notes': 'Worked last weekend'},
                {'leave_date': date.today() - timedelta(days=30), 'leave_type': 'Other', 'notes': 'Personal appointment with long description to test wrapping or truncation.'}
            ]
            meeting_data = [
                {'meeting_date': date.today() - timedelta(days=2), 'meeting_details': 'Project Alpha Sync: Discussed milestones and blockers.'},
                {'meeting_date': date.today() - timedelta(days=15), 'meeting_details': 'Client Onboarding Call - Phase 1. Very long details to see how the treeview handles it, hopefully it wraps or has a scrollbar or something similar.'}
            ]
        else:
            db_conn = None
            try:
                db_conn = connect_db()
                if db_conn:
                    leave_data = get_recent_records(db_conn, 'leave_records')
                    meeting_data = get_recent_records(db_conn, 'meeting_records')
                else:
                    messagebox.showerror("Database Error", "Failed to connect to retrieve recent records.")
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred while fetching recent records: {e}")
            finally:
                if db_conn:
                    db_conn.close()

        # Column map: treeview column ID -> data dictionary key
        leave_column_map = {'date': 'leave_date', 'type': 'leave_type', 'notes': 'notes'}
        self._populate_treeview(self.recent_leave_tree, leave_data, leave_column_map)

        meeting_column_map = {'date': 'meeting_date', 'details': 'meeting_details'}
        self._populate_treeview(self.recent_meetings_tree, meeting_data, meeting_column_map)

    def _export_data_action(self):
        leave_data = []
        meeting_data = []

        if USE_PLACEHOLDER_DATA:
            messagebox.showinfo("Export Info", "Exporting placeholder data. Excel export might generate an empty file if not fully simulated.")
            # Use the same placeholder data as in _update_recent_records_display for consistency
            leave_data = [
                {'leave_date': date.today() - timedelta(days=1), 'leave_type': 'Annual Leave', 'notes': 'Quick break', 'status': 'active'},
                {'leave_date': date.today() - timedelta(days=30), 'leave_type': 'Other', 'notes': 'Personal', 'status': 'cancelled'}
            ]
            meeting_data = [
                {'meeting_date': date.today() - timedelta(days=2), 'meeting_details': 'Project Alpha Sync', 'status': 'active'},
                {'meeting_date': date.today() - timedelta(days=15), 'meeting_details': 'Client Onboarding', 'status': 'active'}
            ]
        else:
            db_conn = None
            try:
                db_conn = connect_db()
                if not db_conn:
                    messagebox.showerror("Database Error", "Failed to connect to the database for export.")
                    return
                leave_data = get_all_records(db_conn, 'leave_records')
                meeting_data = get_all_records(db_conn, 'meeting_records')
            except Exception as e:
                messagebox.showerror("Database Error", f"Error fetching data for export: {e}")
                return # Stop if data fetch fails
            finally:
                if db_conn:
                    db_conn.close()

        if not leave_data and not meeting_data:
            messagebox.showinfo("Export Info", "No data available to export.")
            return

        # --- Excel Export ---
        if self.excel_export_possible:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Save Data as Excel"
            )
            if filepath:
                try:
                    wb = openpyxl.Workbook()
                    # Leave Records sheet
                    ws_leave = wb.active
                    ws_leave.title = "Leave Records"
                    leave_headers = ["Date", "Type", "Notes", "Status"]
                    ws_leave.append(leave_headers)
                    for record in leave_data:
                        ws_leave.append([
                            record.get('leave_date').strftime("%Y-%m-%d") if isinstance(record.get('leave_date'), date) else record.get('leave_date'),
                            record.get('leave_type', ''),
                            record.get('notes', ''),
                            record.get('status', '')
                        ])

                    # Meeting Records sheet
                    if meeting_data: # Only create if there's data
                        ws_meetings = wb.create_sheet("Meeting Records")
                        meeting_headers = ["Date", "Details", "Status"]
                        ws_meetings.append(meeting_headers)
                        for record in meeting_data:
                            ws_meetings.append([
                                record.get('meeting_date').strftime("%Y-%m-%d") if isinstance(record.get('meeting_date'), date) else record.get('meeting_date'),
                                record.get('meeting_details', ''),
                                record.get('status', '')
                            ])
                    wb.save(filepath)
                    messagebox.showinfo("Excel Export", f"Data successfully exported to\n{filepath}")
                except Exception as e:
                    messagebox.showerror("Excel Export Error", f"Failed to export data to Excel: {e}")
            else:
                messagebox.showinfo("Excel Export", "Excel export cancelled by user.")
        else:
            messagebox.showwarning("Excel Export Skipped", "Openpyxl library not found. Cannot export to Excel.")

        # --- TXT Pop-up Display ---
        txt_content = "--- Leave Records ---\n"
        if leave_data:
            for record in leave_data:
                dt = record.get('leave_date').strftime("%Y-%m-%d") if isinstance(record.get('leave_date'), date) else record.get('leave_date', 'N/A')
                tp = record.get('leave_type', 'N/A')
                nt = record.get('notes', 'N/A').replace('\n', ' ') # Replace newlines for single line display
                st = record.get('status', 'N/A')
                txt_content += f"Date: {dt}, Type: {tp}, Notes: {nt}, Status: {st}\n"
        else:
            txt_content += "No leave records.\n"

        txt_content += "\n--- Meeting Records ---\n"
        if meeting_data:
            for record in meeting_data:
                dt = record.get('meeting_date').strftime("%Y-%m-%d") if isinstance(record.get('meeting_date'), date) else record.get('meeting_date', 'N/A')
                det = record.get('meeting_details', 'N/A').replace('\n', ' ') # Replace newlines
                st = record.get('status', 'N/A')
                txt_content += f"Date: {dt}, Details: {det}, Status: {st}\n"
        else:
            txt_content += "No meeting records.\n"

        # Create Toplevel window for TXT display
        txt_popup = Toplevel(self)
        txt_popup.title("Data Export (TXT)")
        txt_popup.geometry("700x500") # Reasonable default size

        text_frame = ttk.Frame(txt_popup)
        text_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        text_widget = Text(text_frame, wrap=tk.WORD, font=("Courier", 9)) # Monospaced font
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        text_widget.insert(tk.END, txt_content)
        text_widget.config(state='disabled') # Make read-only

        txt_popup.transient(self) # Keep it on top of the main window
        txt_popup.grab_set()      # Make it modal
        self.wait_window(txt_popup) # Wait until it's closed


if __name__ == "__main__":
    app = App()
    app.mainloop()
