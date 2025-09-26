import tkinter as tk
from tkinter import ttk, simpledialog, filedialog, messagebox
from tkcalendar import Calendar
import datetime
from system_monitor import SystemMonitor
import excel_exporter
from db_manager import DatabaseManager, DB_CONFIG # For DB status messages
import mysql.connector # For specific DB error handling

# --- Highlight Colors for Calendar Events ---
HIGHLIGHT_COLOR_VACATION = "pink"
HIGHLIGHT_COLOR_MEETING = "lightgreen"
HIGHLIGHT_COLOR_CANCELLED = "#B0B0B0"
HIGHLIGHT_COLOR_BOTH_ACTIVE = "#FF6347" # Tomato Red
HIGHLIGHT_COLOR_RANGE_SELECT_TEMP = "gold"

# --- Theme Constants (Windows XP Gemstone Blue inspired) ---
XP_BLUE_DARK = "#0053B4"
XP_BLUE_MEDIUM = "#3B7DD8"
XP_BLUE_LIGHT = "#A0D2F5"
XP_FRAME_BG = "#D4E8F7"
XP_CALENDAR_BG = "#FFFFFF"
XP_INPUT_AREA_BG = XP_FRAME_BG
XP_TREEVIEW_BG = "#F0F8FF"
XP_TREEVIEW_FIELD_BG = "#FFFFFF"
XP_TREEVIEW_HEADING_BG = XP_FRAME_BG
XP_STATUS_BAR_BG = XP_FRAME_BG
XP_POPUP_BG = XP_FRAME_BG

XP_GREY_LIGHT = "#F0F0F0"
XP_WHITE = "#FFFFFF"
XP_BLACK = "#000000"
XP_BUTTON_TEXT = "#000000"

WINDOW_TRANSPARENCY = 0.95

class VacationApp:
    """Main application class for the Vacation & Meeting Tracker."""
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("休假与会议记录备忘 (Vacation & Meeting Tracker)")
        self.root.geometry("1250x800")
        self.root.configure(bg=XP_BLUE_MEDIUM)

        self.db = None
        try:
            # print("Initializing DatabaseManager...") # Debug: Removed
            self.db = DatabaseManager()
            # print("DatabaseManager initialized successfully.") # Informative, but better for console of db_manager
        except mysql.connector.Error as db_err:
            messagebox.showerror(
                "数据库连接失败 (Database Connection Failed)",
                f"无法连接到数据库 '{DB_CONFIG.get('database', 'N/A')}' 于主机 '{DB_CONFIG.get('host', 'N/A')}'.\n"
                f"错误: {db_err}\n应用程序将关闭。",
                parent=self.root
            )
            self.root.destroy()
            return
        except Exception as e:
            messagebox.showerror(
                "初始化错误 (Initialization Error)",
                f"应用程序初始化期间发生严重错误: {e}\n应用程序将关闭。",
                parent=self.root
            )
            self.root.destroy()
            return

        try:
            self.root.attributes('-alpha', WINDOW_TRANSPARENCY)
        except tk.TclError:
            pass # Silently ignore if transparency is not supported

        self.sys_mon = SystemMonitor()
        self.current_display_year = datetime.date.today().year
        self.current_display_month = datetime.date.today().month
        self.active_calendar_selected_date = None
        self.selected_date_details = None
        self.is_range_select_mode = tk.BooleanVar(value=False)
        self.range_start_date = None
        self.temp_range_highlight_ids_cal1 = []
        self.temp_range_highlight_ids_cal2 = []
        self.remark_options = ["年休假", "家长会", "倒休", "其他"]
        self.remark_type_var = tk.StringVar()

        self.setup_styles()
        self.create_main_layout()

        self.update_calendar_display_dates()
        self.update_action_buttons_state()
        self.clear_selection_and_inputs() # Initialize input fields and selections
        self.update_recent_records_list() # Initial population of recent records
        self.update_status_bar_tick() # Start status bar updates

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        # print("VacationApp UI fully initialized.") # Debug: Removed

    def on_closing(self):
        """Handles window close event to ensure database connection is closed."""
        # print("Closing application via on_closing...") # Debug: Removed
        if self.db:
            try: self.db.close(); # print("Database connection closed via on_closing.") # Debug: Removed
            except Exception as e: print(f"Error closing database during on_closing: {e}") # Keep for error logging
        self.root.destroy()

    def setup_styles(self):
        """Configures ttk styles for the application, aiming for an XP-like theme."""
        self.style = ttk.Style()
        available_themes = self.style.theme_names()
        if 'clam' in available_themes: self.style.theme_use('clam')
        elif 'alt' in available_themes: self.style.theme_use('alt')
        else: self.style.theme_use('default')

        # General Frames and Backgrounds
        self.style.configure("TFrame", background=XP_BLUE_MEDIUM)
        self.style.configure("Content.TFrame", background=XP_FRAME_BG)
        self.style.configure("ActionsPanel.TFrame", background=XP_BLUE_MEDIUM)

        # Calendar Area Styles
        self.style.configure("CalendarNav.TFrame", background=XP_FRAME_BG)
        self.style.configure("CalendarMain.TFrame", background=XP_FRAME_BG)
        self.style.configure("CalendarInner.TFrame", background=XP_CALENDAR_BG)

        # LabelFrame Styles
        self.style.configure("TLabelframe", background=XP_FRAME_BG, relief=tk.GROOVE, borderwidth=1, padding=5)
        self.style.configure("TLabelframe.Label", background=XP_FRAME_BG, foreground=XP_BLUE_DARK, font=('Arial', 11, 'bold'))
        self.style.configure("InputSection.TLabelFrame", background=XP_INPUT_AREA_BG) # Inherits TLabelframe, specific if needed
        self.style.configure("InputSection.TLabelFrame.Label", background=XP_INPUT_AREA_BG, foreground=XP_BLUE_DARK)
        self.style.configure("ActionButtons.TLabelFrame", background=XP_FRAME_BG) # Inherits TLabelframe
        self.style.configure("ActionButtons.TLabelFrame.Label", background=XP_FRAME_BG, foreground=XP_BLUE_DARK)
        self.style.configure("RecentRecords.TLabelFrame", background=XP_FRAME_BG) # Inherits TLabelframe
        self.style.configure("RecentRecords.TLabelFrame.Label", background=XP_FRAME_BG, foreground=XP_BLUE_DARK)

        # Label Styles
        self.style.configure("TLabel", background=XP_BLUE_MEDIUM, foreground=XP_BLACK, font=('Arial', 10))
        self.style.configure("Content.TLabel", background=XP_FRAME_BG, foreground=XP_BLACK, font=('Arial', 10))
        self.style.configure("Input.TLabel", background=XP_INPUT_AREA_BG, foreground=XP_BLACK, font=('Arial', 10))
        self.style.configure("StatusInfo.TLabel", background=XP_INPUT_AREA_BG, foreground=XP_BLACK, font=('Arial', 10, 'italic'), wraplength=380)
        self.style.configure("CalendarHeader.TLabel", background=XP_FRAME_BG, foreground=XP_BLUE_DARK, font=('Arial', 12, 'bold'))
        self.style.configure("CalendarSubHeader.TLabel", background=XP_CALENDAR_BG, foreground=XP_BLUE_DARK, font=('Arial', 10, 'bold'))

        # Entry and OptionMenu Styles
        self.style.configure("TEntry", font=('Arial', 10), padding=3)
        self.style.configure("TOptionMenu", font=('Arial', 10), padding=3)

        # Button Styles
        self.style.configure("TButton", font=('Arial', 10, 'bold'), padding=(8, 4), relief=tk.RAISED, borderwidth=1)
        self.style.map("TButton",
                       background=[('active', XP_BLUE_DARK), ('!disabled', XP_BLUE_LIGHT)],
                       foreground=[('active', XP_WHITE), ('!disabled', XP_BUTTON_TEXT)],
                       relief=[('pressed', tk.SUNKEN), ('!pressed', tk.RAISED)])
        self.style.configure("Nav.TButton", font=('Arial', 10, 'bold'), padding=(10,5)) # Calendar navigation

        # Checkbutton Style
        self.style.configure("TCheckbutton", background=XP_FRAME_BG, font=('Arial', 10), indicatorrelief=tk.FLAT)
        self.style.map("TCheckbutton", indicatorbackground=[('!selected', XP_WHITE), ('selected', XP_BLUE_DARK)], foreground=[('focus', XP_BLUE_DARK)])

        # Notebook and Treeview Styles
        self.style.configure("TNotebook", background=XP_FRAME_BG, tabmargins=[2, 5, 2, 0])
        self.style.configure("TNotebook.Tab", font=('Arial', 10, 'bold'), padding=[8, 4], background=XP_BLUE_LIGHT, foreground=XP_BLACK)
        self.style.map("TNotebook.Tab", background=[("selected", XP_FRAME_BG), ('!selected', XP_BLUE_LIGHT)], foreground=[("selected", XP_BLUE_DARK)], bordercolor=[("selected", XP_BLUE_DARK)])
        self.style.configure("Treeview", background=XP_TREEVIEW_BG, fieldbackground=XP_TREEVIEW_FIELD_BG, foreground=XP_BLACK, font=('Arial', 9), rowheight=22)
        self.style.configure("Treeview.Heading", font=('Arial', 10, 'bold'), background=XP_TREEVIEW_HEADING_BG, foreground=XP_BLUE_DARK, relief=tk.RAISED, padding=(5,3))
        self.style.map("Treeview.Heading", background=[('active', XP_BLUE_MEDIUM)], relief=[('active', tk.GROOVE)])
        self.style.map("Treeview", background=[('selected', XP_BLUE_DARK)], foreground=[('selected', XP_WHITE)])

        # Status Bar Styles
        self.style.configure("StatusBar.TFrame", background=XP_STATUS_BAR_BG, relief=tk.SUNKEN, borderwidth=1)
        self.style.configure("StatusBar.TLabel", background=XP_STATUS_BAR_BG, foreground=XP_BLACK, font=('Arial', 9))

        # Popup Text Widget (using tk.Text, not ttk.Text, so styled directly)
        # No ttk style needed for tk.Text, styled at instantiation.

    def create_main_layout(self):
        self.main_container = ttk.Frame(self.root, style="TFrame", padding=10); self.main_container.pack(fill=tk.BOTH, expand=True)
        self.top_area_frame = ttk.Frame(self.main_container, style="Content.TFrame"); self.top_area_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.create_calendar_area()
        self.create_actions_panel_area()
        self.bottom_area_frame = ttk.Frame(self.main_container, style="StatusBar.TFrame", height=28); self.bottom_area_frame.pack(fill=tk.X, expand=False, side=tk.BOTTOM, pady=(5,0))
        self.create_status_bar()

    def create_status_bar(self):
        status_bar_frame = ttk.Frame(self.bottom_area_frame, style="StatusBar.TFrame", padding=(2,2))
        status_bar_frame.pack(fill=tk.BOTH, expand=True)
        self.time_label = ttk.Label(status_bar_frame, text="Time: --", style="StatusBar.TLabel", relief=tk.SUNKEN, padding=(5,2)); self.time_label.pack(side=tk.LEFT, padx=(0,2))
        self.mem_label = ttk.Label(status_bar_frame, text="Memory: --%", style="StatusBar.TLabel", relief=tk.SUNKEN, padding=(5,2)); self.mem_label.pack(side=tk.LEFT, padx=(0,2))
        self.net_label = ttk.Label(status_bar_frame, text="Network: D: -- U: -- KB/s", style="StatusBar.TLabel", relief=tk.SUNKEN, padding=(5,2)); self.net_label.pack(side=tk.LEFT, padx=(0,2))

    def update_status_bar_tick(self):
        if not self.root.winfo_exists(): return
        try:
            self.time_label.config(text=f"Time: {self.sys_mon.get_current_time()}")
            self.mem_label.config(text=f"Memory: {self.sys_mon.get_memory_usage_percent():.1f}%")
            down, up = self.sys_mon.get_network_speed_kbytes_per_sec()
            self.net_label.config(text=f"Network: D: {down:.1f} U: {up:.1f} KB/s")
        except Exception as e:
            # print(f"Error updating status bar: {e}") # Keep for debugging if status bar fails
            if hasattr(self, 'time_label') and self.time_label.winfo_exists(): self.time_label.config(text="Time: Error")
        self.root.after(1000, self.update_status_bar_tick)

    def create_actions_panel_area(self):
        self.actions_panel_frame = ttk.Frame(self.top_area_frame, style="Content.TFrame", padding=5)
        self.actions_panel_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10,0))
        details_input_frame = ttk.LabelFrame(self.actions_panel_frame, text="详情/输入", style="InputSection.TLabelFrame", padding=10); details_input_frame.pack(fill=tk.X, pady=(0,5), expand=False)
        self.remarks_info_label = ttk.Label(details_input_frame, text="请选择日期.", style="StatusInfo.TLabel"); self.remarks_info_label.pack(pady=(0,10), fill=tk.X)
        type_label = ttk.Label(details_input_frame, text="类型:", style="Input.TLabel"); type_label.pack(fill=tk.X, pady=(0,2))
        self.remark_type_menu = ttk.OptionMenu(details_input_frame, self.remark_type_var, self.remark_options[0], *self.remark_options, command=self.on_remark_type_changed); self.remark_type_menu.pack(fill=tk.X, pady=(0,5))
        other_remark_label = ttk.Label(details_input_frame, text="备注 ('其他'):", style="Input.TLabel"); other_remark_label.pack(fill=tk.X, pady=(0,2))
        self.other_remark_entry = ttk.Entry(details_input_frame, font=('Arial', 10), state=tk.DISABLED, style="TEntry"); self.other_remark_entry.pack(fill=tk.X, pady=(0,10))
        action_buttons_frame = ttk.LabelFrame(self.actions_panel_frame, text="功能按钮", style="ActionButtons.TLabelFrame", padding=10); action_buttons_frame.pack(fill=tk.X, pady=5, expand=False)
        self.add_vacation_button = ttk.Button(action_buttons_frame, text="添加休假", command=self.process_add_vacation, state=tk.DISABLED); self.add_vacation_button.pack(fill=tk.X, pady=3)
        self.add_meeting_button = ttk.Button(action_buttons_frame, text="添加会议", command=self.process_add_meeting, state=tk.DISABLED); self.add_meeting_button.pack(fill=tk.X, pady=3)
        self.range_select_checkbutton = ttk.Checkbutton(action_buttons_frame, text="连续选择日期", variable=self.is_range_select_mode, command=self.toggle_range_select_mode, style="TCheckbutton"); self.range_select_checkbutton.pack(fill=tk.X, pady=3, anchor='w')
        self.delete_button = ttk.Button(action_buttons_frame, text="删除记录", command=self.process_delete_entry, state=tk.DISABLED); self.delete_button.pack(fill=tk.X, pady=3)
        self.export_button = ttk.Button(action_buttons_frame, text="导出数据", command=self.process_export_data); self.export_button.pack(fill=tk.X, pady=3)
        self.create_recent_records_display(self.actions_panel_frame)

    def create_recent_records_display(self, parent_frame):
        recent_records_frame = ttk.LabelFrame(parent_frame, text="最近一年记录", style="RecentRecords.TLabelFrame", padding=10); recent_records_frame.pack(fill=tk.BOTH, expand=True, pady=(10,0))
        self.recent_records_notebook = ttk.Notebook(recent_records_frame, style="TNotebook"); self.recent_records_notebook.pack(fill=tk.BOTH, expand=True)
        vacations_tab_frame = ttk.Frame(self.recent_records_notebook, style="Content.TFrame", padding=(5,5)); self.recent_records_notebook.add(vacations_tab_frame, text='休假记录')
        cols_vacation = ("日期", "类型", "备注", "状态"); self.recent_vacations_tree = ttk.Treeview(vacations_tab_frame, columns=cols_vacation, show='headings', style="Treeview")
        for col in cols_vacation: self.recent_vacations_tree.heading(col, text=col); self.recent_vacations_tree.column(col, width=150 if col=="备注" else 100, anchor=tk.W if col=="备注" else tk.CENTER, minwidth=60)
        vac_scrollbar = ttk.Scrollbar(vacations_tab_frame, orient="vertical", command=self.recent_vacations_tree.yview); self.recent_vacations_tree.configure(yscrollcommand=vac_scrollbar.set); vac_scrollbar.pack(side=tk.RIGHT, fill=tk.Y); self.recent_vacations_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        meetings_tab_frame = ttk.Frame(self.recent_records_notebook, style="Content.TFrame", padding=(5,5)); self.recent_records_notebook.add(meetings_tab_frame, text='会议记录')
        cols_meeting = ("日期", "内容", "状态"); self.recent_meetings_tree = ttk.Treeview(meetings_tab_frame, columns=cols_meeting, show='headings', style="Treeview")
        for col in cols_meeting: self.recent_meetings_tree.heading(col, text=col); self.recent_meetings_tree.column(col, width=200 if col=="内容" else 100, anchor=tk.W if col=="内容" else tk.CENTER, minwidth=60)
        meet_scrollbar = ttk.Scrollbar(meetings_tab_frame, orient="vertical", command=self.recent_meetings_tree.yview); self.recent_meetings_tree.configure(yscrollcommand=meet_scrollbar.set); meet_scrollbar.pack(side=tk.RIGHT, fill=tk.Y); self.recent_meetings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def on_remark_type_changed(self, selected_type):
        if selected_type == "其他": self.other_remark_entry.config(state=tk.NORMAL)
        else: self.other_remark_entry.delete(0, tk.END); self.other_remark_entry.config(state=tk.DISABLED)

    def create_calendar_area(self):
        calendar_outer_frame = ttk.LabelFrame(self.top_area_frame, text="日历视图", padding=10, style="TLabelframe")
        calendar_outer_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,5))
        nav_frame = ttk.Frame(calendar_outer_frame, style="CalendarNav.TFrame"); nav_frame.pack(pady=5, fill=tk.X)
        ttk.Button(nav_frame, text="<< 上个月", command=self.prev_month_pair, style="Nav.TButton").pack(side=tk.LEFT, padx=10)
        self.current_month_year_label = ttk.Label(nav_frame, text="YYYY年 MM月", style="CalendarHeader.TLabel", anchor='center'); self.current_month_year_label.pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(nav_frame, text="下个月 >>", command=self.next_month_pair, style="Nav.TButton").pack(side=tk.RIGHT, padx=10)
        calendars_frame = ttk.Frame(calendar_outer_frame, style="CalendarMain.TFrame"); calendars_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        cal_style_props = {'background': XP_BLUE_DARK, 'foreground': XP_WHITE, 'bordercolor': XP_BLUE_DARK,'headersbackground': XP_BLUE_MEDIUM, 'headersforeground': XP_WHITE,'normalbackground': XP_CALENDAR_BG, 'normalforeground': XP_BLACK,'weekendbackground': XP_CALENDAR_BG, 'weekendforeground': XP_BLUE_DARK,'othermonthbackground': XP_GREY_LIGHT, 'othermonthforeground': "dim gray",'othermonthwebackground': XP_GREY_LIGHT, 'othermonthweforeground': "dark gray",'selectbackground': XP_BLUE_DARK, 'selectforeground': XP_WHITE,'font': ('Arial', 9), 'headersfont': ('Arial', 9, 'bold'),'showweeknumbers': False, 'firstweekday': 'monday', 'date_pattern': 'yyyy-mm-dd'}
        cal1_container = ttk.Frame(calendars_frame, style="CalendarInner.TFrame", padding=2); cal1_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.cal1_month_year_header = ttk.Label(cal1_container, text="M1 YYYY", style="CalendarSubHeader.TLabel", anchor='center'); self.cal1_month_year_header.pack(pady=(0,3), fill=tk.X)
        self.cal1 = Calendar(cal1_container, **cal_style_props); self.cal1.pack(fill=tk.BOTH, expand=True)
        cal2_container = ttk.Frame(calendars_frame, style="CalendarInner.TFrame", padding=2); cal2_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.cal2_month_year_header = ttk.Label(cal2_container, text="M2 YYYY", style="CalendarSubHeader.TLabel", anchor='center'); self.cal2_month_year_header.pack(pady=(0,3), fill=tk.X)
        self.cal2 = Calendar(cal2_container, **cal_style_props); self.cal2.pack(fill=tk.BOTH, expand=True)
        tags = {'vacation': HIGHLIGHT_COLOR_VACATION, 'meeting': HIGHLIGHT_COLOR_MEETING, 'cancelled': HIGHLIGHT_COLOR_CANCELLED, 'both_active': HIGHLIGHT_COLOR_BOTH_ACTIVE, 'range_select_temp': HIGHLIGHT_COLOR_RANGE_SELECT_TEMP}
        for cal in [self.cal1, self.cal2]:
            for tag_name, color in tags.items(): fg_color = XP_WHITE if tag_name == 'both_active' else XP_BLACK; cal.tag_config(tag_name, background=color, foreground=fg_color)
        self.cal1.bind("<<CalendarSelected>>", lambda e: self.on_calendar_date_selected(e, self.cal1)); self.cal2.bind("<<CalendarSelected>>", lambda e: self.on_calendar_date_selected(e, self.cal2))
        self.cal1.bind("<B1-Motion>", lambda e: self.on_calendar_drag(e, self.cal1)); self.cal2.bind("<B1-Motion>", lambda e: self.on_calendar_drag(e, self.cal2))
        self.cal1.bind("<ButtonRelease-1>", lambda e: self.on_calendar_drag_end(e, self.cal1)); self.cal2.bind("<ButtonRelease-1>", lambda e: self.on_calendar_drag_end(e, self.cal2))

    def load_and_highlight_dates(self):
        if not self.db: return
        for cal in [self.cal1, self.cal2]: cal.calevent_remove('all')
        m1_date = self.cal1.display_date; m2_date = self.cal2.display_date
        start_date_view = datetime.date(min(m1_date.year, m2_date.year), min(m1_date.month, m2_date.month), 1)
        max_year = max(m1_date.year, m2_date.year); max_month = max(m1_date.month, m2_date.month)
        try: end_date_view = (datetime.date(max_year, max_month, 1).replace(month=max_month+1)) - datetime.timedelta(days=1)
        except ValueError: end_date_view = datetime.date(max_year, 12, 31)
        try: records = self.db.get_records_in_date_range(start_date_view, end_date_view)
        except mysql.connector.Error as db_err: messagebox.showwarning("数据库错误", f"加载日历数据失败: {db_err}", parent=self.root); return
        except Exception as e: messagebox.showwarning("错误", f"加载日历数据时发生未知错误: {e}", parent=self.root); return
        if not records: return
        events_on_date = {}
        for vac in records.get('vacations', []): date_obj = vac['vacation_date']; events_on_date.setdefault(date_obj, {})['vac'] = vac
        for meet in records.get('meetings', []): date_obj = meet['meeting_date']; events_on_date.setdefault(date_obj, {})['meet'] = meet
        for date_obj, event_info in events_on_date.items():
            vac_info = event_info.get('vac'); meet_info = event_info.get('meet'); tag_to_apply = None; event_text = ""
            is_vac_active = vac_info and not vac_info.get('cancelled', 0); is_meet_active = meet_info and not meet_info.get('cancelled', 0)
            if is_vac_active and is_meet_active: tag_to_apply = 'both_active'; event_text = f"休+会"
            elif is_vac_active: tag_to_apply = 'vacation'; event_text = vac_info.get('type', '休假')[:2]
            elif is_meet_active: tag_to_apply = 'meeting'; event_text = meet_info.get('content', '会议')[:2]
            elif vac_info or meet_info : tag_to_apply = 'cancelled'; event_text = "取消"
            if tag_to_apply:
                for cal in [self.cal1, self.cal2]:
                    cal_disp_year, cal_disp_month = cal.display_date.year, cal.display_date.month
                    if date_obj.year == cal_disp_year and date_obj.month == cal_disp_month:
                        try: cal.calevent_create(date_obj, event_text, tag_to_apply)
                        except Exception: pass

    def on_calendar_date_selected(self, event, calendar_widget):
        try: selected_date_str = calendar_widget.get_date(); current_selected_date = datetime.datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        except Exception as e: self.remarks_info_label.config(text=f"错误: 解析日期失败"); return
        self.active_calendar_selected_date = current_selected_date
        self.selected_date_details = {'date': current_selected_date}
        if self.is_range_select_mode.get():
            if not self.range_start_date: self.range_start_date = current_selected_date; self.clear_temp_range_highlights(); self.highlight_date_range_temp(self.range_start_date, self.range_start_date); self.remarks_info_label.config(text=f"范围开始: {self.range_start_date.strftime('%Y-%m-%d')}.")
            else: actual_start = min(self.range_start_date, current_selected_date); actual_end = max(self.range_start_date, current_selected_date); self.highlight_date_range_temp(actual_start, actual_end); self.remarks_info_label.config(text=f"范围: {actual_start.strftime('%Y-%m-%d')} 至 {actual_end.strftime('%Y-%m-%d')}.")
        else:
            self.range_start_date = None; self.clear_temp_range_highlights(); info_text = f"选定: {current_selected_date.strftime('%Y-%m-%d')}.\n"
            if self.db:
                try:
                    vac_info = self.db.get_vacation_by_date(current_selected_date); meet_info = self.db.get_meeting_by_date(current_selected_date)
                    self.selected_date_details.update({'vacation': vac_info, 'meeting': meet_info})
                    if vac_info: info_text += f"休假: {vac_info['type']} ({'已取消' if vac_info['cancelled'] else '有效'}).\n"
                    else: info_text += "当日无休假记录.\n"
                    if meet_info: info_text += f"会议: {meet_info['content'][:10]}{'...' if len(meet_info['content']) > 10 else ''} ({'已取消' if meet_info['cancelled'] else '有效'})."
                    else: info_text += "当日无会议安排."
                except mysql.connector.Error as db_err: info_text += f"无法获取详情: {db_err}"; messagebox.showwarning("数据库读取错误", f"获取日期详情失败: {db_err}", parent=self.root)
                except Exception as e: info_text += f"获取详情时发生未知错误: {e}"; messagebox.showwarning("错误", f"获取日期详情时发生未知错误: {e}", parent=self.root)
            else: info_text += "数据库未连接."
            self.remarks_info_label.config(text=info_text)
            if calendar_widget == self.cal1 and self.cal2.selection_get(): self.cal2.selection_clear()
            elif calendar_widget == self.cal2 and self.cal1.selection_get(): self.cal1.selection_clear()
        self.update_action_buttons_state()

    def on_calendar_drag(self, event, calendar_widget):
        if self.is_range_select_mode.get() and self.range_start_date:
            try: date_at_cursor_str = calendar_widget.get_date(); date_at_cursor = datetime.datetime.strptime(date_at_cursor_str, "%Y-%m-%d").date()
            except Exception: return
            if date_at_cursor: actual_start = min(self.range_start_date, date_at_cursor); actual_end = max(self.range_start_date, date_at_cursor); self.highlight_date_range_temp(actual_start, actual_end); self.remarks_info_label.config(text=f"选择中: {actual_start.strftime('%Y-%m-%d')} 至 {actual_end.strftime('%Y-%m-%d')}")

    def on_calendar_drag_end(self, event, calendar_widget):
        if self.is_range_select_mode.get() and self.range_start_date:
            if self.active_calendar_selected_date: actual_start = min(self.range_start_date, self.active_calendar_selected_date); actual_end = max(self.range_start_date, self.active_calendar_selected_date); self.highlight_date_range_temp(actual_start, actual_end); self.remarks_info_label.config(text=f"范围: {actual_start.strftime('%Y-%m-%d')} 至 {actual_end.strftime('%Y-%m-%d')}.")
            else: self.remarks_info_label.config(text="范围选择无效.")
            self.update_action_buttons_state()

    def highlight_date_range_temp(self, start_date, end_date):
        self.clear_temp_range_highlights(); current_date = start_date
        while current_date <= end_date:
            for cal, ids_list in [(self.cal1, self.temp_range_highlight_ids_cal1), (self.cal2, self.temp_range_highlight_ids_cal2)]:
                cal_disp_year, cal_disp_month = cal.display_date.year, cal.display_date.month
                if current_date.year == cal_disp_year and current_date.month == cal_disp_month:
                    try: ev_id = cal.calevent_create(current_date, '', 'range_select_temp'); ids_list.append(ev_id)
                    except Exception: pass
            current_date += datetime.timedelta(days=1)

    def clear_temp_range_highlights(self):
        for cal, ids_list in [(self.cal1, self.temp_range_highlight_ids_cal1), (self.cal2, self.temp_range_highlight_ids_cal2)]:
            for ev_id in ids_list:
                try: cal.calevent_remove(ev_id) # Add try-except in case event was already removed or invalid
                except Exception: pass
            ids_list.clear()

    def update_action_buttons_state(self):
        is_range_mode = self.is_range_select_mode.get(); valid_single_date = self.active_calendar_selected_date and not is_range_mode
        valid_range = is_range_mode and self.range_start_date and self.active_calendar_selected_date and self.range_start_date != self.active_calendar_selected_date
        self.add_vacation_button.config(state=tk.NORMAL if valid_single_date or valid_range else tk.DISABLED)
        self.add_meeting_button.config(state=tk.NORMAL if valid_single_date or valid_range else tk.DISABLED)
        can_delete = False
        if valid_single_date and self.selected_date_details:
            vac = self.selected_date_details.get('vacation'); meet = self.selected_date_details.get('meeting')
            if (vac and not vac['cancelled']) or (meet and not meet['cancelled']): can_delete = True
        self.delete_button.config(state=tk.NORMAL if can_delete else tk.DISABLED)

    def clear_selection_and_inputs(self):
        self.active_calendar_selected_date = None; self.range_start_date = None; self.selected_date_details = None
        self.clear_temp_range_highlights()
        if hasattr(self, 'cal1') and self.cal1.winfo_exists() and self.cal1.selection_get(): self.cal1.selection_clear()
        if hasattr(self, 'cal2') and self.cal2.winfo_exists() and self.cal2.selection_get(): self.cal2.selection_clear()
        self.remark_type_var.set(self.remark_options[0]);
        if hasattr(self, 'other_remark_entry'): self.other_remark_entry.delete(0, tk.END); self.other_remark_entry.config(state=tk.DISABLED)
        if hasattr(self, 'remarks_info_label'): self.remarks_info_label.config(text="请选择日期或日期范围.")
        if hasattr(self, 'add_vacation_button'): self.update_action_buttons_state()

    def toggle_range_select_mode(self):
        self.clear_selection_and_inputs()
        if self.is_range_select_mode.get(): self.remarks_info_label.config(text="范围选择模式激活. 点击选择开始日期.")
        else: self.remarks_info_label.config(text="单日选择模式激活.")

    def update_recent_records_list(self):
        for item in self.recent_vacations_tree.get_children(): self.recent_vacations_tree.delete(item)
        for item in self.recent_meetings_tree.get_children(): self.recent_meetings_tree.delete(item)
        if not self.db: return
        try:
            recent_data = self.db.get_recent_records();
            if recent_data:
                for vac in recent_data.get('vacations', []): self.recent_vacations_tree.insert('', tk.END, values=(excel_exporter.format_value_for_display(vac.get('vacation_date')), vac.get('type', ''), vac.get('remarks', ''), "已取消" if vac.get('cancelled') else "有效"))
                for meet in recent_data.get('meetings', []): self.recent_meetings_tree.insert('', tk.END, values=(excel_exporter.format_value_for_display(meet.get('meeting_date')), meet.get('content', ''), "已取消" if meet.get('cancelled') else "有效"))
        except mysql.connector.Error as db_err: messagebox.showwarning("数据库错误", f"加载最近记录失败: {db_err}", parent=self.root)
        except Exception as e: messagebox.showwarning("错误", f"加载最近记录时发生未知错误: {e}", parent=self.root)

    def process_add_vacation(self):
        if not self.db: messagebox.showerror("错误", "数据库未连接。", parent=self.root); return
        vac_type = self.remark_type_var.get(); remarks = self.other_remark_entry.get().strip() if vac_type == "其他" else ""
        if vac_type == "其他" and not remarks: messagebox.showwarning("输入错误", "选择“其他”类型时备注不能为空。", parent=self.root); return
        dates_to_process = [];
        if self.is_range_select_mode.get() and self.range_start_date and self.active_calendar_selected_date: start_date = min(self.range_start_date, self.active_calendar_selected_date); end_date = max(self.range_start_date, self.active_calendar_selected_date); current_date = start_date; while current_date <= end_date: dates_to_process.append(current_date); current_date += datetime.timedelta(days=1)
        elif self.active_calendar_selected_date: dates_to_process.append(self.active_calendar_selected_date)
        else: messagebox.showwarning("注意", "请先选择一个日期或日期范围。", parent=self.root); return
        added_count = 0; skipped_count = 0
        try:
            for date_obj in dates_to_process:
                existing_meeting = self.db.get_meeting_by_date(date_obj)
                if existing_meeting and not existing_meeting.get('cancelled'):
                    if not messagebox.askyesno("冲突警告", f"{date_obj.strftime('%Y-%m-%d')} 已有有效会议。确定要覆盖添加休假吗？", parent=self.root): skipped_count +=1; continue
                res = self.db.add_or_update_vacation(date_obj, vac_type, remarks)
                if res is None: raise Exception(f"添加休假失败 {date_obj}")
                added_count +=1
            msg = f"{added_count} 天休假已添加。"
            if skipped_count > 0: msg += f"\n{skipped_count} 天因会议冲突跳过。"
            messagebox.showinfo("成功", msg, parent=self.root)
        except mysql.connector.Error as db_err: messagebox.showerror("数据库操作失败", f"添加休假失败: {db_err}", parent=self.root)
        except Exception as e: messagebox.showerror("操作失败", f"添加休假时发生错误: {e}", parent=self.root)
        self.load_and_highlight_dates(); self.update_recent_records_list(); self.clear_selection_and_inputs()

    def process_add_meeting(self):
        if not self.db: messagebox.showerror("错误", "数据库未连接。", parent=self.root); return
        meeting_content = simpledialog.askstring("会议内容", "请输入会议内容:", parent=self.root)
        if not meeting_content or not meeting_content.strip(): messagebox.showwarning("输入错误", "会议内容不能为空。", parent=self.root); return
        dates_to_process = [];
        if self.active_calendar_selected_date: dates_to_process.append(min(self.range_start_date, self.active_calendar_selected_date) if self.is_range_select_mode.get() and self.range_start_date else self.active_calendar_selected_date)
        else: messagebox.showwarning("注意", "请先选择一个日期。", parent=self.root); return
        added_count = 0; skipped_count = 0
        try:
            for date_obj in dates_to_process:
                existing_vacation = self.db.get_vacation_by_date(date_obj)
                if existing_vacation and not existing_vacation.get('cancelled'):
                     if not messagebox.askyesno("冲突警告", f"{date_obj.strftime('%Y-%m-%d')} 已有有效休假。确定要覆盖添加会议吗？", parent=self.root): skipped_count +=1; continue
                res = self.db.add_or_update_meeting(date_obj, meeting_content)
                if res is None: raise Exception(f"添加会议失败 {date_obj}")
                added_count +=1
            msg = f"{added_count} 个会议已添加。"
            if skipped_count > 0: msg += f"\n{skipped_count} 个因休假冲突跳过。"
            messagebox.showinfo("成功", msg, parent=self.root)
        except mysql.connector.Error as db_err: messagebox.showerror("数据库操作失败", f"添加会议失败: {db_err}", parent=self.root)
        except Exception as e: messagebox.showerror("操作失败", f"添加会议时发生错误: {e}", parent=self.root)
        self.load_and_highlight_dates(); self.update_recent_records_list(); self.clear_selection_and_inputs()

    def process_delete_entry(self):
        if not self.db : messagebox.showerror("错误", "数据库未连接。", parent=self.root); return
        if not self.active_calendar_selected_date or self.is_range_select_mode.get() or not self.selected_date_details: messagebox.showwarning("注意", "请选择一个包含有效记录的单独日期进行删除。", parent=self.root); return
        date_to_delete = self.selected_date_details['date']; vac_info = self.selected_date_details.get('vacation'); meet_info = self.selected_date_details.get('meeting')
        item_to_delete = None; item_type_for_msg = ""
        active_vac = vac_info and not vac_info['cancelled']; active_meet = meet_info and not meet_info['cancelled']
        if active_vac and active_meet:
            choice = simpledialog.askstring("选择删除类型", "当日同时存在有效休假和会议。\n请输入 '休假' 或 '会议' 指定删除项:", parent=self.root)
            if choice and choice.lower() in ["vacation", "休假"]: item_to_delete = "vacation"; item_type_for_msg = "休假"
            elif choice and choice.lower() in ["meeting", "会议"]: item_to_delete = "meeting"; item_type_for_msg = "会议"
            else: messagebox.showinfo("取消", "未选择删除类型或输入无效。", parent=self.root); return
        elif active_vac: item_to_delete = "vacation"; item_type_for_msg = "休假"
        elif active_meet: item_to_delete = "meeting"; item_type_for_msg = "会议"
        else: messagebox.showinfo("提示", f"{date_to_delete.strftime('%Y-%m-%d')} 无有效记录可删除或已取消。", parent=self.root); return
        reason = simpledialog.askstring("删除原因", f"请输入取消 {item_type_for_msg} 的原因 (可选):", parent=self.root)
        if reason is None: reason = ""
        try:
            success = False
            if item_to_delete == "vacation": success = self.db.cancel_vacation(date_to_delete, reason)
            elif item_to_delete == "meeting": success = self.db.cancel_meeting(date_to_delete, reason)
            if success: messagebox.showinfo("成功", f"{date_to_delete.strftime('%Y-%m-%d')} 的 {item_type_for_msg} 已标记为取消。", parent=self.root)
            else: messagebox.showerror("操作失败", f"取消 {item_type_for_msg} 失败。可能记录不存在或已被取消。", parent=self.root)
        except mysql.connector.Error as db_err: messagebox.showerror("数据库操作失败", f"取消 {item_type_for_msg} 失败: {db_err}", parent=self.root)
        except Exception as e: messagebox.showerror("操作失败", f"取消 {item_type_for_msg} 时发生错误: {e}", parent=self.root)
        self.load_and_highlight_dates(); self.update_recent_records_list(); self.clear_selection_and_inputs()

    def process_export_data(self):
        if not self.db: messagebox.showerror("错误", "数据库未连接。", parent=self.root); return
        try:
            all_data = self.db.get_all_records_for_export()
            if all_data is None: raise Exception("未能从数据库检索到数据。")
            vacations_data = all_data.get('vacations', []); meetings_data = all_data.get('meetings', [])
            if not vacations_data and not meetings_data: messagebox.showinfo("无数据", "数据库中没有可导出的记录。", parent=self.root); return
            filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel 工作簿", "*.xlsx"), ("所有文件", "*.*")], title="导出数据为 Excel", parent=self.root)
            if not filepath: return
            success = excel_exporter.export_data_to_excel(vacations_data, meetings_data, filepath)
            if success: messagebox.showinfo("导出成功", f"数据已成功导出到:\n{filepath}", parent=self.root); txt_content = excel_exporter.generate_txt_content(vacations_data, meetings_data); self.show_txt_popup("导出数据预览 (TXT)", txt_content)
            else: messagebox.showerror("导出失败", "无法保存 Excel 文件。可能是文件权限问题或路径无效。", parent=self.root)
        except mysql.connector.Error as db_err: messagebox.showerror("数据库错误", f"导出数据失败: {db_err}", parent=self.root)
        except Exception as e: messagebox.showerror("导出错误", f"导出过程中发生错误: {e}", parent=self.root)

    def show_txt_popup(self, title, content):
        popup = tk.Toplevel(self.root); popup.title(title); popup.configure(bg=XP_POPUP_BG); popup.geometry("600x400")
        try: popup.transient(self.root); popup.grab_set()
        except tk.TclError: pass # Ignore if fails (e.g. during rapid init/close)
        text_frame = ttk.Frame(popup, padding=5, style="Content.TFrame"); text_frame.pack(fill=tk.BOTH, expand=True)
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Courier New', 9), relief=tk.SOLID, borderwidth=1, background=XP_WHITE, foreground=XP_BLACK, padx=5, pady=5); text_widget.insert(tk.END, content); text_widget.config(state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview); text_widget['yscrollcommand'] = scrollbar.set
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y); text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        button_frame = ttk.Frame(popup, padding=(5,10), style="Content.TFrame"); button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Button(button_frame, text="关闭", command=popup.destroy).pack()
        popup.wait_window()

    def update_calendar_display_dates(self):
        y1 = self.current_display_year; m1 = self.current_display_month; self.cal1.display_date = datetime.date(y1, m1, 1); self.cal1_month_year_header.config(text=f"{y1}年 {m1:02d}月")
        m2 = m1 + 1; y2 = y1;
        if m2 > 12: m2 = 1; y2 += 1
        self.cal2.display_date = datetime.date(y2, m2, 1); self.cal2_month_year_header.config(text=f"{y2}年 {m2:02d}月")
        self.current_month_year_label.config(text=f"{y1}年 {m1:02d}月  |  {y2}年 {m2:02d}月");
        self.clear_temp_range_highlights()
        self.load_and_highlight_dates()

    def prev_month_pair(self):
        self.current_display_month -= 1
        if self.current_display_month < 1: self.current_display_month = 12; self.current_display_year -= 1
        self.update_calendar_display_dates(); self.clear_selection_and_inputs()

    def next_month_pair(self):
        self.current_display_month += 1
        if self.current_display_month > 12: self.current_display_month = 1; self.current_display_year += 1
        self.update_calendar_display_dates(); self.clear_selection_and_inputs()

if __name__ == '__main__':
    root = tk.Tk()
    app = None
    try:
        app = VacationApp(root)
    except Exception as e:
        # This general exception catch is for unforeseen errors during VacationApp instantiation
        # that might occur after the DB check in __init__ or if root window becomes invalid.
        err_msg = f"启动应用程序时发生关键错误: {e}\n应用程序将关闭。"
        print(err_msg) # Also print to console for headless environments
        try:
            if root.winfo_exists(): # Check if root window can still show messagebox
                 messagebox.showerror("应用程序错误 (Application Error)", err_msg, parent=root)
        finally:
            if root.winfo_exists(): root.destroy()
        app = None

    if app and app.db is not None: # Check app and app.db to ensure __init__ was successful
        root.mainloop()
    else:
        # print("Application did not start due to initialization or database connection failure.") # Already handled by __init__ or above
        if root.winfo_exists(): root.destroy() # Ensure window is closed if not already
