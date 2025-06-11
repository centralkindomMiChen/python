import tkinter as tk
from tkinter import ttk
import calendar # Standard Python library
from datetime import datetime, timedelta, date # Added date

# Define highlight colors
HIGHLIGHT_COLORS = {
    "leave": "#FFC0CB",       # Pink
    "meeting": "#90EE90",     # Light Green
    "leave_and_meeting": "#FF7F50", # Coral (similar to Red, but distinct)
    "cancelled": "#D3D3D3",   # Gray
    "today_default": "#B0E0E6", # Powder blue for today if no other highlight
    "normal_day": "SystemButtonFace" # Default button color
}

class CustomCalendar(ttk.Frame):
    def __init__(self, parent, year=None, month=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.current_year = year if year else datetime.now().year
        self.current_month = month if month else datetime.now().month

        self._leave_dates = set()
        self._meeting_dates = set()
        self._cancelled_dates = set()

        # Style for ttk buttons (used for date cells)
        # It's better to configure styles on the root window once, if possible,
        # but for a self-contained widget, this is acceptable.
        self.style = ttk.Style(self)
        # Note: ttk theming can be complex. Backgrounds on TButton are not always directly supported
        # on all themes (e.g. on macOS with aqua theme). For more robust styling,
        # one might need to use tk.Button or draw custom widgets.
        # These .configure calls are attempts, actual appearance may vary by OS/theme.
        self.style.configure("Leave.TButton", background=HIGHLIGHT_COLORS["leave"])
        self.style.configure("Meeting.TButton", background=HIGHLIGHT_COLORS["meeting"])
        self.style.configure("LeaveMeeting.TButton", background=HIGHLIGHT_COLORS["leave_and_meeting"])
        self.style.configure("Cancelled.TButton", background=HIGHLIGHT_COLORS["cancelled"])
        self.style.configure("Today.TButton", background=HIGHLIGHT_COLORS["today_default"])
        # For text color, ttk usually handles contrast, but it can be set with 'foreground'

        # Frame for Month/Year Label
        self.header_frame = ttk.Frame(self)
        self.header_frame.pack(pady=2) # Reduced padding

        self.month_year_label = ttk.Label(self.header_frame, text="", font=("Arial", 12, "bold"), width=15, anchor="center")
        self.month_year_label.pack(side=tk.LEFT, padx=5)

        self.days_frame = ttk.Frame(self)
        self.days_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        self.on_date_select_callback = None # Callback for when a date is selected

        self.draw_calendar() # Initial draw

    def set_highlight_dates(self, leave_dates=None, meeting_dates=None, cancelled_dates=None):
        """
        Stores sets of datetime.date objects to be highlighted.
        Call draw_calendar() afterwards to apply changes.
        """
        self._leave_dates = leave_dates if leave_dates else set()
        self._meeting_dates = meeting_dates if meeting_dates else set()
        self._cancelled_dates = cancelled_dates if cancelled_dates else set()
        # Note: Does not redraw automatically. Caller should call draw_calendar().

    def set_date(self, year, month):
        """
        Sets the calendar to a specific year and month.
        Call draw_calendar() afterwards to reflect the change and apply highlights.
        """
        self.current_year = year
        self.current_month = month
        # self.draw_calendar() # Removed: main_app should call draw_calendar

    def _date_clicked(self, year, month, day):
        # Placeholder for date click handling
        clicked_date_obj = date(year, month, day)
        print(f"Date clicked: {clicked_date_obj.strftime('%Y-%m-%d')}")
        if self.on_date_select_callback:
            self.on_date_select_callback(clicked_date_obj)


    def draw_calendar(self):
        """Draws the calendar days, applying highlighting based on stored dates."""
        # Clear previous days
        for widget in self.days_frame.winfo_children():
            widget.destroy()

        self.month_year_label.config(text=f"{calendar.month_name[self.current_month]} {self.current_year}")

        # Day headers
        days_of_week = ["M", "Tu", "W", "Th", "F", "Sa", "Su"] # Shortened for space
        for i, day_name in enumerate(days_of_week):
            ttk.Label(self.days_frame, text=day_name, font=("Arial", 9, "bold"), width=3, anchor="center").grid(row=0, column=i, padx=1, pady=1)

        month_calendar = calendar.monthcalendar(self.current_year, self.current_month)

        for row_idx, week in enumerate(month_calendar, start=1):
            for col_idx, day_num in enumerate(week):
                if day_num == 0:
                    ttk.Label(self.days_frame, text="", width=3, anchor="center").grid(row=row_idx, column=col_idx, padx=1, pady=1)
                else:
                    # Determine the style for the button
                    # IMPORTANT: ttk.Button styling for background is theme-dependent.
                    # What works on one OS/theme might not on another (e.g., some themes ignore background).
                    # For truly custom backgrounds, a tk.Canvas or tk.Label might be more reliable.
                    # Here, we attempt with ttk.Style, which is the "correct" ttk way.

                    current_day_date_obj = date(self.current_year, self.current_month, day_num)
                    today_date_obj = date.today()

                    is_today = (current_day_date_obj == today_date_obj)
                    is_leave = current_day_date_obj in self._leave_dates
                    is_meeting = current_day_date_obj in self._meeting_dates
                    is_cancelled = current_day_date_obj in self._cancelled_dates

                    button_style_name = ""
                    bg_color = HIGHLIGHT_COLORS["normal_day"] # Default

                    if is_cancelled:
                        button_style_name = "Cancelled.TButton"
                        bg_color = HIGHLIGHT_COLORS["cancelled"]
                    elif is_leave and is_meeting:
                        button_style_name = "LeaveMeeting.TButton"
                        bg_color = HIGHLIGHT_COLORS["leave_and_meeting"]
                    elif is_leave:
                        button_style_name = "Leave.TButton"
                        bg_color = HIGHLIGHT_COLORS["leave"]
                    elif is_meeting:
                        button_style_name = "Meeting.TButton"
                        bg_color = HIGHLIGHT_COLORS["meeting"]
                    elif is_today:
                        button_style_name = "Today.TButton"
                        bg_color = HIGHLIGHT_COLORS["today_default"]

                    # Fallback for themes where ttk.Button background doesn't work well:
                    # We can use a tk.Label and bind click to it, or a tk.Button.
                    # For simplicity with ttk structure, we'll try to make TButton work.
                    # If button_style_name is empty, it uses the default TButton style.
                    day_button = ttk.Button(
                        self.days_frame,
                        text=str(day_num),
                        width=2, # Keep small for fitting
                        command=lambda d=day_num: self._date_clicked(self.current_year, self.current_month, d),
                        style=button_style_name if button_style_name else "TButton" # Apply style
                    )
                    day_button.grid(row=row_idx, column=col_idx, padx=1, pady=1, sticky="nsew")

                    # For some ttk themes, explicitly setting relief for "today" might be needed if style alone isn't enough
                    if is_today and not button_style_name: # If it's today and no other highlight applied
                         day_button.config(relief="solid") # Default TButton but with relief for today

        # Configure column/row weights for the days_frame to make buttons fill cells
        for i in range(7): # 7 columns for days of week
            self.days_frame.grid_columnconfigure(i, weight=1)
        # Assuming max 6 weeks for a month + 1 header row
        for i in range(1, 7): # Rows for weeks (1 to 6)
             self.days_frame.grid_rowconfigure(i, weight=1)


    def get_date(self):
        """Returns the first day (as a datetime.date object) of the currently displayed month and year."""
        return date(self.current_year, self.current_month, 1)

# Example usage (for testing this file directly)
if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("300x370") # Adjusted for better single calendar view
    root.title("Custom Calendar Test")

    # Use datetime.date for consistency
    current_display_dt_obj = date.today()

    cal_container = ttk.Frame(root)
    cal_container.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)

    nav_frame = ttk.Frame(cal_container)
    nav_frame.pack(pady=5)

    month_year_label_var = tk.StringVar(value=current_display_dt_obj.strftime("%B %Y"))
    ttk.Label(nav_frame, textvariable=month_year_label_var).pack(side=tk.LEFT, padx=5)

    test_cal = CustomCalendar(cal_container, year=current_display_dt_obj.year, month=current_display_dt_obj.month)
    test_cal.pack(expand=True, fill=tk.BOTH)

    def apply_changes_and_redraw(new_date_obj):
        global current_display_dt_obj # Make sure to use the global one
        current_display_dt_obj = new_date_obj

        # 1. Update calendar's internal date (year, month)
        test_cal.set_date(current_display_dt_obj.year, current_display_dt_obj.month)
        month_year_label_var.set(current_display_dt_obj.strftime("%B %Y"))

        # 2. (Simulate fetching data) & Set highlight dates
        print(f"Simulating data fetch for {current_display_dt_obj.year}-{current_display_dt_obj.month}")
        # Sample data should use datetime.date objects
        sample_leave = {
            date(current_display_dt_obj.year, current_display_dt_obj.month, 5),
            date(current_display_dt_obj.year, current_display_dt_obj.month, 15)
        }
        sample_meetings = {
            date(current_display_dt_obj.year, current_display_dt_obj.month, 10),
            date(current_display_dt_obj.year, current_display_dt_obj.month, 15) # Overlap with leave
        }
        sample_cancelled = {
            date(current_display_dt_obj.year, current_display_dt_obj.month, 20)
        }
        test_cal.set_highlight_dates(
            leave_dates=sample_leave,
            meeting_dates=sample_meetings,
            cancelled_dates=sample_cancelled
        )

        # 3. Redraw the calendar to apply changes and highlights
        test_cal.draw_calendar()

    def on_prev_month_test():
        first_of_current = current_display_dt_obj.replace(day=1)
        prev_month_date_obj = (first_of_current - timedelta(days=1)).replace(day=1)
        apply_changes_and_redraw(prev_month_date_obj)

    def on_next_month_test():
        first_of_current = current_display_dt_obj.replace(day=1)
        next_month_date_obj = (first_of_current + timedelta(days=32)).replace(day=1)
        apply_changes_and_redraw(next_month_date_obj)

    ttk.Button(nav_frame, text="<", command=on_prev_month_test).pack(side=tk.LEFT)
    ttk.Button(nav_frame, text=">", command=on_next_month_test).pack(side=tk.LEFT)

    # Initial data load for the first view
    apply_changes_and_redraw(current_display_dt_obj)

    def print_selected_date_test(selected_date_obj_param):
        print("Selected in test:", selected_date_obj_param.strftime("%Y-%m-%d"))

    test_cal.on_date_select_callback = print_selected_date_test

    root.mainloop()
