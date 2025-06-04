import tkinter as tk
from tkinter import ttk, messagebox, simpledialog # Added simpledialog
from tkinter import filedialog # For asking save location
from tkcalendar import Calendar
import datetime
import db_manager
import excel_exporter # For our new module
import system_monitor # For our new module

# --- Theme Constants ---
APP_BG_COLOR = "#62A9E1"
FRAME_BG_COLOR = "#D4E8F7"
TEXT_COLOR = "#000000"
BUTTON_BG_COLOR = "#A0D2F5"
BUTTON_FG_COLOR = "#000000"
HIGHLIGHT_COLOR_VACATION = "pink"
HIGHLIGHT_COLOR_MEETING = "#90EE90"
HIGHLIGHT_COLOR_CANCELLED = "grey"
SELECT_BG_COLOR_CALENDAR = "#77A2D9"
WINDOW_TRANSPARENCY = 0.95

class VacationApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("休假与会议记录备忘 (Vacation & Meeting Tracker)")
        self.root.geometry("1000x750")
        self.root.configure(bg=APP_BG_COLOR)

        try:
            self.db = db_manager.DatabaseManager()
        except ConnectionError as e:
            try:
                messagebox.showerror("数据库连接失败", f"无法连接到数据库: {e}\n请检查MySQL服务配置。\n程序退出。")
            except tk.TclError:
                print(f"CRITICAL: DB Connection Failed: {e}. Tkinter messagebox failed.")
            self.root.destroy()
            return

        # Initialize SystemMonitor
        self.sys_mon = system_monitor.SystemMonitor()

        try:
            self.root.attributes('-alpha', WINDOW_TRANSPARENCY)
        except tk.TclError:
            print("Info: Window transparency not supported.")

        self.current_display_year = datetime.date.today().year
        self.current_display_month = datetime.date.today().month

        self.active_calendar_selected_date = None
        self.selected_date_details = None # To store details of the selected date from DB

        # For range selection
        self.is_range_select_mode = tk.BooleanVar(value=False)
        self.range_start_date = None
        self.temp_range_highlight_ids_cal1 = [] # To store temp event IDs for range highlight
        self.temp_range_highlight_ids_cal2 = []


        self.setup_styles()
        self.create_main_layout()
        self.create_calendar_area()
        self.create_remarks_and_actions_area()
        self.create_recent_records_area()
        self.create_status_bar()

        self.update_calendar_display_dates()
        self.update_recent_records_list() # Initial population
        self.update_status_bar_tick() # Start the status bar update loop
        print("UI with Input Logic Initialized.")

    def setup_styles(self):
        self.style = ttk.Style()
        available_themes = self.style.theme_names()
        if 'clam' in available_themes: self.style.theme_use('clam')
        elif 'alt' in available_themes: self.style.theme_use('alt')

        self.style.configure("TFrame", background=APP_BG_COLOR)
        self.style.configure("CustomNav.TFrame", background=FRAME_BG_COLOR)
        self.style.configure("CalendarInner.TFrame", background="white")
        self.style.configure("TLabel", background=APP_BG_COLOR, foreground=TEXT_COLOR, font=('Arial', 10))
        self.style.configure("MonthYear.TLabel", background=FRAME_BG_COLOR, foreground=TEXT_COLOR, font=('Arial', 12, 'bold'))
        self.style.configure("CalendarHeader.TLabel", background="white", foreground=TEXT_COLOR, font=('Arial', 10, 'bold'))
        self.style.configure("TLabelframe", background=FRAME_BG_COLOR, relief=tk.RIDGE, borderwidth=2)
        self.style.configure("TLabelframe.Label", background=FRAME_BG_COLOR, foreground=TEXT_COLOR, font=('Arial', 10, 'bold'))
        self.style.configure("TButton", font=('Arial', 10), padding=5, background=BUTTON_BG_COLOR, foreground=BUTTON_FG_COLOR)
        self.style.map("TButton", background=[('active', '#8DC0E8'), ('disabled', '#C0C0C0')], foreground=[('disabled', '#606060')])
        self.style.configure("Treeview", font=('Arial', 9), rowheight=25)
        self.style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        self.style.configure("Status.TLabel", background=APP_BG_COLOR, foreground=TEXT_COLOR, font=('Arial', 9))
        self.style.configure("Link.TLabel", foreground="blue", font=('Arial', 10, 'underline'))

        self.style.configure("TNotebook", background=APP_BG_COLOR) # Main notebook background
        self.style.configure("TNotebook.Tab", background=FRAME_BG_COLOR, padding=[5, 2]) # Tab buttons
        self.style.map("TNotebook.Tab",
            background=[("selected", APP_BG_COLOR)], # Selected tab background
            foreground=[("selected", TEXT_COLOR)])

        # Style for frames used as content for notebook tabs
        self.style.configure("TabContent.TFrame", background=FRAME_BG_COLOR)


    def create_main_layout(self): # Unchanged
        self.main_container = ttk.Frame(self.root, padding=10)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        self.top_frame = ttk.Frame(self.main_container)
        self.top_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.bottom_frame = ttk.Frame(self.main_container)
        self.bottom_frame.pack(fill=tk.BOTH, expand=True)

    def create_calendar_area(self): # Minor changes for drag binding
        calendar_outer_frame = ttk.LabelFrame(self.top_frame, text="日历视图 (Calendar View)", padding=10)
        calendar_outer_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(0,10))

        nav_frame = ttk.Frame(calendar_outer_frame, style="CustomNav.TFrame")
        nav_frame.pack(pady=5, fill=tk.X)

        ttk.Button(nav_frame, text="<< 上个月 (Prev)", command=self.prev_month_pair).pack(side=tk.LEFT, padx=10)
        self.current_month_year_label = ttk.Label(nav_frame, text="YYYY年 MM月", style="MonthYear.TLabel")
        self.current_month_year_label.pack(side=tk.LEFT, expand=True, fill=tk.X, anchor='center')
        ttk.Button(nav_frame, text="下个月 (Next) >>", command=self.next_month_pair).pack(side=tk.RIGHT, padx=10)

        calendars_frame = ttk.Frame(calendar_outer_frame, style="CustomNav.TFrame")
        calendars_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        cal_props = {
            'selectmode': 'day', 'date_pattern': 'yyyy-mm-dd', 'font': "Arial 9",
            'borderwidth': 1, 'showweeknumbers': False, 'background': APP_BG_COLOR,
            'foreground': TEXT_COLOR, 'headersbackground': FRAME_BG_COLOR,
            'headersforeground': TEXT_COLOR, 'normalbackground': "white",
            'normalforeground': "black", 'weekendbackground': "white",
            'weekendforeground': "black", 'othermonthbackground': "lightgrey",
            'othermonthforeground': "darkgrey", 'othermonthwebackground': "lightgrey",
            'othermonthweforeground': "darkgrey", 'selectbackground': SELECT_BG_COLOR_CALENDAR,
            'selectforeground': "white", 'tooltipdelay': 500,
        }

        self.cal1_frame = ttk.Frame(calendars_frame, style="CalendarInner.TFrame")
        self.cal1_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.cal1_month_year_header_label = ttk.Label(self.cal1_frame, text="月份1", style="CalendarHeader.TLabel", anchor="center")
        self.cal1_month_year_header_label.pack(pady=(0,5), fill=tk.X)
        self.cal1 = Calendar(self.cal1_frame, **cal_props)
        self.cal1.pack(fill=tk.BOTH, expand=True)
        self.cal1.bind("<<CalendarSelected>>", lambda e, cal=self.cal1: self.on_calendar_date_selected(e, cal))
        self.cal1.bind("<B1-Motion>", lambda e, cal=self.cal1: self.on_calendar_drag(e, cal))
        self.cal1.bind("<ButtonRelease-1>", lambda e, cal=self.cal1: self.on_calendar_drag_end(e, cal))


        self.cal2_frame = ttk.Frame(calendars_frame, style="CalendarInner.TFrame")
        self.cal2_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.cal2_month_year_header_label = ttk.Label(self.cal2_frame, text="月份2", style="CalendarHeader.TLabel", anchor="center")
        self.cal2_month_year_header_label.pack(pady=(0,5), fill=tk.X)
        self.cal2 = Calendar(self.cal2_frame, **cal_props)
        self.cal2.pack(fill=tk.BOTH, expand=True)
        self.cal2.bind("<<CalendarSelected>>", lambda e, cal=self.cal2: self.on_calendar_date_selected(e, cal))
        self.cal2.bind("<B1-Motion>", lambda e, cal=self.cal2: self.on_calendar_drag(e, cal))
        self.cal2.bind("<ButtonRelease-1>", lambda e, cal=self.cal2: self.on_calendar_drag_end(e, cal))


        for cal_widget in [self.cal1, self.cal2]:
            cal_widget.tag_config('vacation', background=HIGHLIGHT_COLOR_VACATION, foreground='black')
            cal_widget.tag_config('meeting', background=HIGHLIGHT_COLOR_MEETING, foreground='black')
            cal_widget.tag_config('cancelled', background=HIGHLIGHT_COLOR_CANCELLED, foreground='white')
            cal_widget.tag_config('range_select_temp', background='#FFD700') # Gold

    def update_calendar_display_dates(self): # Unchanged
        y1, m1 = self.current_display_year, self.current_display_month
        self.cal1.display_date = datetime.date(y1, m1, 1)
        self.cal1_month_year_header_label.config(text=f"{y1}年 {m1:02d}月")
        if m1 == 12: y2_actual, m2_actual = y1 + 1, 1
        else: y2_actual, m2_actual = y1, m1 + 1
        self.cal2.display_date = datetime.date(y2_actual, m2_actual, 1)
        self.cal2_month_year_header_label.config(text=f"{y2_actual}年 {m2_actual:02d}月")
        self.current_month_year_label.config(text=f"{y1}年 {m1:02d}月  |  {y2_actual}年 {m2_actual:02d}月")
        self.load_and_highlight_dates()

    def prev_month_pair(self): # Unchanged
        self.current_display_month -= 1
        if self.current_display_month < 1:
            self.current_display_month = 12; self.current_display_year -= 1
        self.update_calendar_display_dates()

    def next_month_pair(self): # Unchanged
        self.current_display_month += 1
        if self.current_display_month > 12:
            self.current_display_month = 1; self.current_display_year += 1
        self.update_calendar_display_dates()

    def load_and_highlight_dates(self): # Minor change to clear temp range highlights
        for cal in [self.cal1, self.cal2]:
            cal.calevent_remove('all')
            for tag_name in ['vacation', 'meeting', 'cancelled', 'range_select_temp']: # Add range_select_temp
                cal.tag_delete(tag_name)
            cal.tag_config('vacation', background=HIGHLIGHT_COLOR_VACATION, foreground='black')
            cal.tag_config('meeting', background=HIGHLIGHT_COLOR_MEETING, foreground='black')
            cal.tag_config('cancelled', background=HIGHLIGHT_COLOR_CANCELLED, foreground='white')
            cal.tag_config('range_select_temp', background='#FFD700') # Re-config

        self.temp_range_highlight_ids_cal1 = [] # Clear stored temp event IDs
        self.temp_range_highlight_ids_cal2 = []

        y1_cal, m1_cal = self.cal1.display_date.year, self.cal1.display_date.month
        if m1_cal == 12: y2_cal, m2_cal = y1_cal + 1, 1
        else: y2_cal, m2_cal = y1_cal, m1_cal + 1
        start_date_view = datetime.date(y1_cal, m1_cal, 1)
        if m2_cal == 12: end_date_view = datetime.date(y2_cal, m2_cal, 31)
        else: end_date_view = datetime.date(y2_cal if m2_cal + 1 <= 12 else y2_cal + 1, (m2_cal + 1) if m2_cal + 1 <= 12 else 1, 1) - datetime.timedelta(days=1)

        if not self.db or not hasattr(self.db, 'conn') or not self.db.conn:
            print("Error: DB not available for loading dates.")
            return

        db_records = self.db.get_records_in_date_range(start_date_view, end_date_view)
        if db_records:
            for rec_type, records_list in db_records.items():
                if not records_list: continue
                for record in records_list:
                    date_obj, tag_to_apply, event_text = None, None, ""
                    if rec_type == 'vacations':
                        date_obj = record.get('vacation_date');_type=record.get('type','')
                        remarks=record.get('remarks',''); cancelled=record.get('cancelled',0)
                        if not date_obj: continue
                        tag_to_apply = 'cancelled' if cancelled else 'vacation'
                        event_text = _type + (f" ({remarks})" if remarks else "")
                        if cancelled: event_text = "取消: " + event_text
                    elif rec_type == 'meetings':
                        date_obj = record.get('meeting_date'); content=record.get('content','')
                        cancelled=record.get('cancelled',0)
                        if not date_obj: continue
                        tag_to_apply = 'cancelled' if cancelled else 'meeting'
                        event_text = content
                        if cancelled: event_text = "取消: " + event_text

                    if date_obj and tag_to_apply:
                        if isinstance(date_obj, str):
                            try: date_obj = datetime.datetime.strptime(date_obj, '%Y-%m-%d').date()
                            except ValueError: continue
                        elif not isinstance(date_obj, datetime.date):
                            if hasattr(date_obj, 'date'): date_obj = date_obj.date() # Handle if it's a datetime object
                            else: continue # Skip if not a convertible type
                        for cal_widget in [self.cal1, self.cal2]:
                            if date_obj.year == cal_widget.display_date.year and date_obj.month == cal_widget.display_date.month:
                                try: cal_widget.calevent_create(date_obj, event_text, tag_to_apply)
                                except Exception as e: print(f"Error creating event {date_obj} tag {tag_to_apply}: {e}")
        if self.active_calendar_selected_date: # Re-select if any
            for cal_widget in [self.cal1, self.cal2]:
                if self.active_calendar_selected_date.year == cal_widget.display_date.year and self.active_calendar_selected_date.month == cal_widget.display_date.month:
                    try: cal_widget.selection_set(self.active_calendar_selected_date)
                    except: pass

    def on_calendar_date_selected(self, event, calendar_widget):
        selected_date_str = calendar_widget.get_date()
        try:
            current_selected_date = datetime.datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            self.active_calendar_selected_date = None; self.selected_date_details = None
            self.remarks_info_label.config(text="无效日期格式 (Invalid date format)")
            return

        if self.is_range_select_mode.get():
            if not self.range_start_date:
                self.range_start_date = current_selected_date
                self.active_calendar_selected_date = None # Clear single selection focus
                self.selected_date_details = None
                self.remarks_info_label.config(text=f"范围开始 (Range Start): {self.range_start_date}\n请选择结束日期 (Select end date).")
                self.highlight_date_range_temp(self.range_start_date, self.range_start_date) # Highlight start
            else: # Range start date already exists, this is the end date
                end_date = current_selected_date
                # Ensure start is before end
                start = min(self.range_start_date, end_date)
                end = max(self.range_start_date, end_date)
                self.active_calendar_selected_date = end_date # Keep active_calendar_selected_date as the end of range
                self.selected_date_details = None
                self.remarks_info_label.config(text=f"范围选择 (Range Selected): {start} to {end}\n请选择类型并添加 (Select type & add).")
                self.highlight_date_range_temp(start, end)
                # self.range_start_date is kept until add action, then cleared.
            self.update_action_buttons_state() # Update buttons for range selection
            return # In range select mode, don't fetch single date details yet

        # Single date selection mode
        self.active_calendar_selected_date = current_selected_date
        self.range_start_date = None # Clear any pending range start
        self.clear_temp_range_highlights()


        # Fetch details for the selected date
        vac_info = self.db.get_vacation_by_date(self.active_calendar_selected_date)
        meet_info = self.db.get_meeting_by_date(self.active_calendar_selected_date)
        self.selected_date_details = {'vacation': vac_info, 'meeting': meet_info, 'date': self.active_calendar_selected_date}

        info_text = f"选中 (Selected): {self.active_calendar_selected_date}\n"
        if vac_info:
            status = "(已取消)" if vac_info['cancelled'] else ""
            info_text += f"休假 {status}: {vac_info['type']} - {vac_info['remarks']}"
        elif meet_info:
            status = "(已取消)" if meet_info['cancelled'] else ""
            info_text += f"会议 {status}: {meet_info['content']}"
        else:
            info_text += "无记录 (No record). 请选择操作 (Select action)."

        self.remarks_info_label.config(text=info_text)
        self.update_action_buttons_state()

        # Clear selection on the other calendar
        other_cal = self.cal2 if calendar_widget == self.cal1 else self.cal1
        try: other_cal.selection_clear()
        except: pass

    def create_remarks_and_actions_area(self):
        remarks_actions_outer_frame = ttk.LabelFrame(self.top_frame, text="操作与备注", padding=10)
        remarks_actions_outer_frame.pack(fill=tk.Y, side=tk.RIGHT, expand=False, ipadx=5)

        remarks_frame = ttk.LabelFrame(remarks_actions_outer_frame, text="详情/输入", padding=5)
        remarks_frame.pack(fill=tk.X, pady=(0,5))
        self.remarks_info_label = ttk.Label(remarks_frame, text="点击日期操作", wraplength=230, justify=tk.LEFT, font=('Arial', 9))
        self.remarks_info_label.pack(pady=5, fill=tk.X,ipady=5)

        remark_input_frame = ttk.Frame(remarks_frame)
        remark_input_frame.pack(fill=tk.X, pady=2)
        ttk.Label(remark_input_frame, text="类型:").grid(row=0, column=0, padx=(0,5), sticky=tk.W)
        self.remark_type_var = tk.StringVar()
        self.remark_options = ["年休假", "家长会", "倒休", "其他"] # Simpler for var
        # self.remark_type_display_options = ["年休假 (Annual)", "家长会 (PTM)", "倒休 (Lieu)", "其他 (Other)"] # If display needed diff
        self.remark_type_var.set(self.remark_options[0])
        # Using simple remark_options for display too for now
        self.remark_menu = ttk.OptionMenu(remark_input_frame, self.remark_type_var, self.remark_options[0], *self.remark_options, command=self.on_remark_type_changed)
        self.remark_menu.grid(row=0, column=1, sticky=tk.EW)

        self.other_remark_label = ttk.Label(remark_input_frame, text="备注:")
        self.other_remark_label.grid(row=1, column=0, padx=(0,5), pady=(2,0), sticky=tk.W)
        self.other_remark_entry = ttk.Entry(remark_input_frame, width=20, state=tk.DISABLED)
        self.other_remark_entry.grid(row=1, column=1, pady=(2,0), sticky=tk.EW)
        remark_input_frame.columnconfigure(1, weight=1)

        actions_frame = ttk.LabelFrame(remarks_actions_outer_frame, text="功能按钮", padding=5)
        actions_frame.pack(fill=tk.X, pady=5)

        self.add_vacation_button = ttk.Button(actions_frame, text="添加休假", command=self.process_add_vacation, state=tk.DISABLED)
        self.add_vacation_button.pack(pady=2, fill=tk.X)

        self.add_meeting_button = ttk.Button(actions_frame, text="添加会议", command=self.process_add_meeting, state=tk.DISABLED)
        self.add_meeting_button.pack(pady=2, fill=tk.X)

        self.range_select_checkbutton = ttk.Checkbutton(actions_frame, text="连续选择日期", variable=self.is_range_select_mode, command=self.toggle_range_select_mode)
        self.range_select_checkbutton.pack(pady=2, anchor=tk.W)

        self.delete_button = ttk.Button(actions_frame, text="删除记录", command=self.process_delete_entry, state=tk.DISABLED)
        self.delete_button.pack(pady=2, fill=tk.X)

        self.export_button = ttk.Button(actions_frame, text="导出数据", command=self.process_export_data)
        self.export_button.pack(pady=2, fill=tk.X)

    def process_export_data(self):
        if not self.db:
            messagebox.showerror("错误 (Error)", "数据库未连接。(Database not connected.)", parent=self.root)
            return

        vacations = self.db.get_all_vacations_for_export()
        meetings = self.db.get_all_meetings_for_export()

        if not vacations and not meetings:
            messagebox.showinfo("无数据 (No Data)", "没有可导出的记录。(No records available to export.)", parent=self.root)
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel 文档 (Excel documents)", "*.xlsx"), ("所有文件 (All files)", "*.*")],
            title="导出记录到 Excel (Export Records to Excel)",
            parent=self.root
        )

        if not filepath: # User cancelled dialog
            return

        try:
            excel_exporter.export_data_to_excel(vacations, meetings, filepath)
            messagebox.showinfo("成功 (Success)", f"数据已成功导出到 (Data successfully exported to):\n{filepath}", parent=self.root)

            # Generate and show TXT content in a popup
            txt_content = excel_exporter.generate_txt_content(vacations, meetings)
            self.show_txt_popup(txt_content)

        except Exception as e:
            messagebox.showerror("导出失败 (Export Failed)", f"导出数据时发生错误 (Error during data export): {e}", parent=self.root)
            import traceback
            traceback.print_exc() # For more detailed error in console

    def show_txt_popup(self, content):
        popup = tk.Toplevel(self.root)
        popup.title("导出数据预览 (TXT Preview)")
        popup.geometry("600x400")
        popup.configure(bg=FRAME_BG_COLOR) # Use a consistent background

        # Make it modal (optional, but good for popups)
        popup.transient(self.root)
        popup.grab_set()

        text_area = tk.Text(popup, wrap=tk.WORD, font=("Courier New", 9),undo=True) # Courier for monospaced, good for TSV like data
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        text_area.insert(tk.END, content)
        text_area.config(state=tk.DISABLED) # Make it read-only

        # Scrollbar for the Text widget
        scrollbar = ttk.Scrollbar(text_area, command=text_area.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_area['yscrollcommand'] = scrollbar.set

        close_button = ttk.Button(popup, text="关闭 (Close)", command=popup.destroy)
        close_button.pack(pady=10)

        self.root.wait_window(popup) # Wait for popup to be closed before returning focus

    def on_remark_type_changed(self, *args):
        if self.remark_type_var.get() == "其他":
            self.other_remark_entry.config(state=tk.NORMAL)
            self.other_remark_entry.focus()
        else:
            self.other_remark_entry.delete(0, tk.END)
            self.other_remark_entry.config(state=tk.DISABLED)

    def update_action_buttons_state(self):
        can_add = False
        # Range mode: if start and end (active_calendar_selected_date) are selected
        if self.is_range_select_mode.get() and self.range_start_date and self.active_calendar_selected_date:
             can_add = True
        # Single date mode: if a date is selected
        elif not self.is_range_select_mode.get() and self.active_calendar_selected_date:
            if self.selected_date_details: # Check if something exists
                vac_exists = self.selected_date_details.get('vacation') and not self.selected_date_details['vacation']['cancelled']
                meet_exists = self.selected_date_details.get('meeting') and not self.selected_date_details['meeting']['cancelled']
                # Allow adding if no active record exists, or if one exists, the other can be added (e.g. add meeting if only vacation exists)
                # This logic might need refinement: current allows adding one type if other exists.
                # For simplicity, let's only allow add if NOTHING active exists on that day to avoid conflict dialogs for now.
                if not vac_exists and not meet_exists: # Only allow add if day is clear
                    can_add = True
            else: # No details usually means no record
                can_add = True

        self.add_vacation_button.config(state=tk.NORMAL if can_add else tk.DISABLED)
        self.add_meeting_button.config(state=tk.NORMAL if can_add else tk.DISABLED)

        can_delete = False
        if not self.is_range_select_mode.get() and self.active_calendar_selected_date and self.selected_date_details:
            vac_exists_active = self.selected_date_details.get('vacation') and not self.selected_date_details['vacation']['cancelled']
            meet_exists_active = self.selected_date_details.get('meeting') and not self.selected_date_details['meeting']['cancelled']
            if vac_exists_active or meet_exists_active:
                can_delete = True
        self.delete_button.config(state=tk.NORMAL if can_delete else tk.DISABLED)


    def process_add_vacation(self):
        vacation_type = self.remark_type_var.get()
        remarks = ""
        if vacation_type == "其他":
            remarks = self.other_remark_entry.get().strip()
            if not remarks:
                messagebox.showwarning("输入错误 (Input Error)", "选择“其他”时备注不能为空。(Remarks cannot be empty for 'Other' type.)", parent=self.root)
                return
        else:
            remarks = self.other_remark_entry.get().strip() # Allow remarks for any type
            if not remarks : remarks = vacation_type # Default remarks to type if entry is empty

        dates_to_process = []
        if self.is_range_select_mode.get() and self.range_start_date and self.active_calendar_selected_date:
            start = min(self.range_start_date, self.active_calendar_selected_date)
            end = max(self.range_start_date, self.active_calendar_selected_date)
            current = start
            while current <= end:
                dates_to_process.append(current)
                current += datetime.timedelta(days=1)
        elif self.active_calendar_selected_date :
             dates_to_process.append(self.active_calendar_selected_date)
        else:
            messagebox.showwarning("选择错误 (Selection Error)", "请先选择日期或日期范围。(Please select a date or date range first.)", parent=self.root)
            return

        added_count = 0
        conflict_dates = []
        for date_obj in dates_to_process:
            existing_meeting = self.db.get_meeting_by_date(date_obj)
            if existing_meeting and not existing_meeting['cancelled']:
                conflict_dates.append(str(date_obj))
                continue

            if self.db.add_vacation(date_obj, vacation_type, remarks):
                added_count += 1
            else:
                print(f"Failed to add/update vacation for {date_obj}")

        if conflict_dates:
            messagebox.showwarning("操作冲突 (Action Conflict)", f"以下日期已存在会议记录，无法添加休假: {', '.join(conflict_dates)}", parent=self.root)

        if added_count > 0:
            messagebox.showinfo("成功 (Success)", f"成功添加/更新 {added_count} 天休假记录。(Successfully added/updated {added_count} vacation day(s).)", parent=self.root)

        self.load_and_highlight_dates()
        self.update_recent_records_list() # <--- ADD THIS
        self.clear_selection_and_inputs()
        # self.update_recent_records_list() # Later
        if self.is_range_select_mode.get():
            self.range_start_date = None; self.active_calendar_selected_date = None
            self.remarks_info_label.config(text="范围已处理。请选择新日期/范围。")


    def process_add_meeting(self):
        content = simpledialog.askstring("会议内容 (Meeting Content)", "请输入会议内容 (Please enter meeting content):", parent=self.root)
        if content is None: return # User cancelled
        if not content.strip():
            messagebox.showwarning("输入错误 (Input Error)", "会议内容不能为空。(Meeting content cannot be empty.)", parent=self.root)
            return

        dates_to_process = []
        if self.is_range_select_mode.get() and self.range_start_date and self.active_calendar_selected_date:
            start = min(self.range_start_date, self.active_calendar_selected_date)
            end = max(self.range_start_date, self.active_calendar_selected_date)
            current = start
            while current <= end:
                dates_to_process.append(current)
                current += datetime.timedelta(days=1)
        elif self.active_calendar_selected_date:
            dates_to_process.append(self.active_calendar_selected_date)
        else:
            messagebox.showwarning("选择错误 (Selection Error)", "请先选择日期或日期范围。(Please select a date or date range first.)", parent=self.root)
            return

        added_count = 0
        conflict_dates = []
        for date_obj in dates_to_process:
            existing_vacation = self.db.get_vacation_by_date(date_obj)
            if existing_vacation and not existing_vacation['cancelled']:
                conflict_dates.append(str(date_obj))
                continue

            if self.db.add_meeting(date_obj, content):
                added_count += 1
            else:
                print(f"Failed to add/update meeting for {date_obj}")

        if conflict_dates:
             messagebox.showwarning("操作冲突 (Action Conflict)", f"以下日期已存在休假记录，无法添加会议: {', '.join(conflict_dates)}", parent=self.root)

        if added_count > 0:
            messagebox.showinfo("成功 (Success)", f"成功添加/更新 {added_count} 天会议记录。(Successfully added/updated {added_count} meeting day(s).)", parent=self.root)

        self.load_and_highlight_dates()
        self.update_recent_records_list() # <--- ADD THIS
        self.clear_selection_and_inputs()
        # self.update_recent_records_list() # Later
        if self.is_range_select_mode.get():
            self.range_start_date = None; self.active_calendar_selected_date = None
            self.remarks_info_label.config(text="范围已处理。请选择新日期/范围。")

    def process_delete_entry(self):
        if not self.active_calendar_selected_date or not self.selected_date_details:
            messagebox.showwarning("选择错误", "请先选择一个有记录的日期进行删除。", parent=self.root)
            return

        date_to_delete = self.active_calendar_selected_date
        item_type_to_delete = None

        vac_info = self.selected_date_details.get('vacation')
        meet_info = self.selected_date_details.get('meeting')

        if vac_info and not vac_info['cancelled']:
            item_type_to_delete = "vacation"
        elif meet_info and not meet_info['cancelled']:
            item_type_to_delete = "meeting"

        if not item_type_to_delete:
            messagebox.showinfo("提示", "所选日期没有可删除的有效记录。", parent=self.root)
            return

        reason = simpledialog.askstring("删除原因 (Deletion Reason)", f"请输入删除 {date_to_delete} 的 {item_type_to_delete} 记录的原因 (可选):", parent=self.root)
        if reason is None: # User cancelled dialog
            return

        success = False
        if item_type_to_delete == "vacation":
            success = self.db.delete_vacation(date_to_delete, reason)
        elif item_type_to_delete == "meeting":
            success = self.db.delete_meeting(date_to_delete, reason)

        if success:
            messagebox.showinfo("成功", f"{date_to_delete} 的 {item_type_to_delete} 记录已标记为取消。", parent=self.root)
            self.load_and_highlight_dates()
            self.update_recent_records_list() # <--- ADD THIS
            self.clear_selection_and_inputs()
        else:
            messagebox.showerror("失败", f"删除 {date_to_delete} 的 {item_type_to_delete} 记录失败。", parent=self.root)
            self.load_and_highlight_dates() # Still refresh calendar
            self.update_recent_records_list() # Still refresh list to ensure consistency
            self.clear_selection_and_inputs()
        # self.update_recent_records_list() # This comment can be removed now


    def toggle_range_select_mode(self):
        self.active_calendar_selected_date = None
        self.selected_date_details = None
        self.range_start_date = None
        self.clear_temp_range_highlights()
        if self.is_range_select_mode.get():
            self.remarks_info_label.config(text="范围选择已启用：\n请点选开始日期。")
        else:
            self.remarks_info_label.config(text="单击日历进行操作。")
        self.update_action_buttons_state()
        try: self.cal1.selection_clear(); self.cal2.selection_clear()
        except: pass


    def highlight_date_range_temp(self, start_date, end_date):
        self.clear_temp_range_highlights()
        current_date = start_date
        while current_date <= end_date:
            for cal_widget, storage_list in [(self.cal1, self.temp_range_highlight_ids_cal1), (self.cal2, self.temp_range_highlight_ids_cal2)]:
                if current_date.year == cal_widget.display_date.year and current_date.month == cal_widget.display_date.month:
                    ev_ids = cal_widget.get_calevents(current_date)
                    is_persistent_highlight = False
                    if ev_ids:
                        for ev_id in ev_ids:
                            event_tags = cal_widget.calevent_cget(ev_id, "tags")
                            if any(tag in event_tags for tag in ['vacation', 'meeting', 'cancelled']):
                                is_persistent_highlight = True; break
                    if not is_persistent_highlight:
                        try:
                            eid = cal_widget.calevent_create(current_date, "范围选择", "range_select_temp")
                            storage_list.append(eid)
                        except Exception as e: print(f"Error creating temp highlight for {current_date}: {e}")
            current_date += datetime.timedelta(days=1)

    def clear_temp_range_highlights(self):
        for cal_widget, storage_list in [(self.cal1, self.temp_range_highlight_ids_cal1), (self.cal2, self.temp_range_highlight_ids_cal2)]:
            for event_id in storage_list:
                try: cal_widget.calevent_remove(event_id)
                except: pass
        self.temp_range_highlight_ids_cal1 = []
        self.temp_range_highlight_ids_cal2 = []


    def on_calendar_drag(self, event, calendar_widget):
        if not self.is_range_select_mode.get() or not self.range_start_date:
            return

        try:
            # Attempt to get date under cursor - this is imperfect with tkcalendar's default events
            # It usually relies on the cell selection changing, which triggers <<CalendarSelected>>
            # For a true pixel-based hit test, one would need to map event.x, event.y to date cells.
            # Here we assume <<CalendarSelected>> will fire if the selected cell changes during drag.
            # So, active_calendar_selected_date gets updated by on_calendar_date_selected.
            if self.active_calendar_selected_date and self.active_calendar_selected_date != self.range_start_date:
                 start = min(self.range_start_date, self.active_calendar_selected_date)
                 end = max(self.range_start_date, self.active_calendar_selected_date)
                 self.highlight_date_range_temp(start, end)
                 self.remarks_info_label.config(text=f"范围: {start} 到 {end}\n释放鼠标以确认结束日期。")
        except Exception as e:
            pass


    def on_calendar_drag_end(self, event, calendar_widget):
        if not self.is_range_select_mode.get() or not self.range_start_date:
            return

        if self.active_calendar_selected_date:
            end_date = self.active_calendar_selected_date
            start = min(self.range_start_date, end_date)
            end = max(self.range_start_date, end_date)
            self.remarks_info_label.config(text=f"范围选定: {start} 到 {end}\n请选择类型并添加。")
            self.highlight_date_range_temp(start, end)
            self.update_action_buttons_state()
        else:
            self.remarks_info_label.config(text=f"范围开始: {self.range_start_date}\n拖拽选择结束日期。")


    def clear_selection_and_inputs(self):
        # Store if was in range mode to potentially restore highlights or clear range_start_date
        was_range_mode = self.is_range_select_mode.get()

        self.active_calendar_selected_date = None
        self.selected_date_details = None
        try:
            self.cal1.selection_clear()
            self.cal2.selection_clear()
        except: pass

        self.other_remark_entry.delete(0, tk.END)
        self.on_remark_type_changed()

        if was_range_mode:
            # If we were in range mode, range_start_date and temp highlights are cleared by process_add or toggle_range_select_mode
            # Here, just ensure UI reflects no specific selection if an operation was completed.
             self.remarks_info_label.config(text="范围选择已启用：\n请点选开始日期。")
        else:
            self.remarks_info_label.config(text="点击日历进行操作。")
            self.clear_temp_range_highlights() # Clear any temp if not in range mode

        # load_and_highlight_dates() is usually called after DB ops, so not always needed here
        # unless clearing selection should revert all temp visual cues.
        # For now, explicit calls to load_and_highlight_dates are made in add/delete methods.
        self.update_action_buttons_state()


    def create_recent_records_area(self): # No structural changes, just ensuring variable names are correct
        recent_frame = ttk.LabelFrame(self.bottom_frame, text="最近一年记录 (Recent Records - Last Year)", padding=10)
        recent_frame.pack(fill=tk.BOTH, expand=True, pady=(0,5)) # Ensure this frame expands

        notebook = ttk.Notebook(recent_frame, style="TNotebook") # Apply notebook style
        notebook.pack(fill=tk.BOTH, expand=True)

        # Vacations Tab
        vacations_tab = ttk.Frame(notebook, padding=5, style="TabContent.TFrame") # Apply tab content style
        notebook.add(vacations_tab, text='休假记录 (Vacations)')
        cols_vacation = ("日期 (Date)", "类型 (Type)", "备注 (Remarks)", "状态 (Status)")
        self.recent_vacations_tree = ttk.Treeview(vacations_tab, columns=cols_vacation, show='headings', height=5) # Reduced height a bit
        for col in cols_vacation:
            self.recent_vacations_tree.heading(col, text=col)
            col_width = 100
            if col == "备注 (Remarks)": col_width = 200
            elif col == "类型 (Type)": col_width = 80
            elif col == "状态 (Status)": col_width = 80
            self.recent_vacations_tree.column(col, width=col_width, anchor=tk.W, stretch=(col == "备注 (Remarks)"))

        vac_scrollbar = ttk.Scrollbar(vacations_tab, orient="vertical", command=self.recent_vacations_tree.yview)
        self.recent_vacations_tree.configure(yscrollcommand=vac_scrollbar.set)
        vac_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.recent_vacations_tree.pack(fill=tk.BOTH, expand=True)

        # Meetings Tab
        meetings_tab = ttk.Frame(notebook, padding=5, style="TabContent.TFrame") # Apply tab content style
        notebook.add(meetings_tab, text='会议记录 (Meetings)')
        cols_meeting = ("日期 (Date)", "内容 (Content)", "状态 (Status)")
        self.recent_meetings_tree = ttk.Treeview(meetings_tab, columns=cols_meeting, show='headings', height=5) # Reduced height
        for col in cols_meeting:
            self.recent_meetings_tree.heading(col, text=col)
            col_width = 100
            if col == "内容 (Content)": col_width = 250
            elif col == "状态 (Status)": col_width = 80
            self.recent_meetings_tree.column(col, width=col_width, anchor=tk.W, stretch=(col == "内容 (Content)"))

        meet_scrollbar = ttk.Scrollbar(meetings_tab, orient="vertical", command=self.recent_meetings_tree.yview)
        self.recent_meetings_tree.configure(yscrollcommand=meet_scrollbar.set)
        meet_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.recent_meetings_tree.pack(fill=tk.BOTH, expand=True)

    def update_recent_records_list(self):
        if not self.db or not hasattr(self.db, 'conn') or not self.db.conn:
            print("DB not available, cannot update recent records list.")
            return

        # Clear existing items from Treeviews
        for item in self.recent_vacations_tree.get_children():
            self.recent_vacations_tree.delete(item)
        for item in self.recent_meetings_tree.get_children():
            self.recent_meetings_tree.delete(item)

        recent_data = self.db.get_recent_records() # Default is last 365 days

        if recent_data.get('vacations'):
            for vac in recent_data['vacations']:
                date_val = excel_exporter.format_value(vac.get('vacation_date')) # Use same formatter
                type_val = vac.get('type', '')
                remarks_val = vac.get('remarks', '')
                status_val = "已取消" if vac.get('cancelled') else "有效"
                self.recent_vacations_tree.insert('', tk.END, values=(date_val, type_val, remarks_val, status_val))

        if recent_data.get('meetings'):
            for meet in recent_data['meetings']:
                date_val = excel_exporter.format_value(meet.get('meeting_date'))
                content_val = meet.get('content', '')
                status_val = "已取消" if meet.get('cancelled') else "有效"
                # Truncate long content for display in treeview if necessary
                display_content = (content_val[:75] + '...') if len(content_val) > 75 else content_val
                self.recent_meetings_tree.insert('', tk.END, values=(date_val, display_content, status_val))

    def create_status_bar(self):
        # Ensure status_bar_frame uses APP_BG_COLOR
        status_bar_frame = ttk.Frame(self.root, relief=tk.SUNKEN, padding=(5,3), style="TFrame") # Explicitly use TFrame style
        status_bar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        # Labels inside will use Status.TLabel which also has APP_BG_COLOR

        self.time_label = ttk.Label(status_bar_frame, text="时间: --", style="Status.TLabel")
        self.time_label.pack(side=tk.LEFT, padx=5)
        self.mem_label = ttk.Label(status_bar_frame, text="内存: --%", style="Status.TLabel")
        self.mem_label.pack(side=tk.LEFT, padx=5)
        self.net_label = ttk.Label(status_bar_frame, text="网络: ↓ -- KB/s ↑ -- KB/s", style="Status.TLabel")
        self.net_label.pack(side=tk.LEFT, padx=5)

    def update_status_bar_tick(self):
        if not hasattr(self, 'root') or not self.root.winfo_exists(): # Stop if window is destroyed
            return

        # Update time
        time_str = self.sys_mon.get_current_time()
        self.time_label.config(text=f"时间 (Time): {time_str}")

        # Update memory usage
        mem_percent = self.sys_mon.get_memory_usage()
        self.mem_label.config(text=f"内存 (Mem): {mem_percent:.1f}%")

        # Update network speed
        try:
            down_speed, up_speed = self.sys_mon.get_network_speed()
            self.net_label.config(text=f"网络 (Net): ↓{down_speed:.1f}KB/s ↑{up_speed:.1f}KB/s")
        except Exception as e:
            # psutil can sometimes raise exceptions on certain platforms or configurations for net_io_counters
            print(f"Error getting network speed: {e}")
            self.net_label.config(text="网络 (Net): Error")


        # Schedule next update (e.g., every 1000ms = 1 second)
        # Check if root window still exists before scheduling next call
        if self.root.winfo_exists():
            self.root.after(1000, self.update_status_bar_tick)


if __name__ == '__main__':
    root = None
    app = None # Define app here to ensure it's in scope for finally
    try:
        root = tk.Tk()
        app = VacationApp(root) # app is assigned here
        # Check if root window was destroyed during VacationApp init (e.g. DB connection failure)
        if root.winfo_exists():
            # Further check if db connection was successful within app object
            if hasattr(app, 'db') and app.db and hasattr(app.db, 'conn') and app.db.conn:
                root.mainloop()
            else:
                # This case should ideally be handled by root.destroy() in __init__,
                # but as a fallback:
                print("Application will not start due to database connection issues.")
                if root.winfo_exists(): root.destroy() # Ensure cleanup
        else:
            print("Application window was destroyed during initialization, likely due to DB connection failure.")

    except tk.TclError as e:
        # This can happen if tkinter itself fails catastrophically, e.g. no display
        print(f"CRITICAL TKINTER ERROR: {e}. Ensure a display environment is available (e.g., Xvfb for headless).")
        if root and root.winfo_exists(): root.destroy()
    except Exception as e:
        print(f"An unexpected critical error occurred: {e}")
        import traceback
        traceback.print_exc()
        if root and root.winfo_exists(): root.destroy()
    finally:
        # Ensure db connection is closed if app and db objects were successfully created
        if app and hasattr(app, 'db') and app.db and hasattr(app.db, 'conn') and app.db.conn:
            if app.db.conn.is_connected(): # Check if connection is still alive
                app.db.close()
                print("Database connection closed via finally block.")
        elif app and hasattr(app, 'db') and app.db and (not hasattr(app.db, 'conn') or not app.db.conn):
             print("DB connection was not established or was closed prematurely.")
        # else:
            # print("App or DB object not fully initialized, no DB connection to close.")
