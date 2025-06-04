import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from tkcalendar import Calendar
import datetime
import db_manager
import system_monitor
import excel_exporter

APP_BG_COLOR = "#3A6EA5"
HIGHLIGHT_COLOR = "pink"
MEETING_HIGHLIGHT_COLOR = "#90EE90"  # Light green for meetings
TEXT_COLOR = "white"
WINDOW_TRANSPARENCY = 0.95

class VacationApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("休假与会议记录备忘")
        self.root.geometry("950x700")

        try:
            self.db = db_manager.DatabaseManager()
        except ConnectionError as e:
            messagebox.showerror("数据库连接失败", f"无法连接到数据库：{e}\n请检查数据库配置和服务器状态。\n程序即将退出。")
            self.root.destroy()
            return
        
        self.sys_mon = system_monitor.SystemMonitor()

        self.current_display_year = datetime.date.today().year
        self.current_display_month = datetime.date.today().month
        
        self.selected_single_date_obj = None
        self.is_range_select_mode = tk.BooleanVar(value=False)
        self.range_start_date_obj = None

        self.setup_styles_and_theme()
        self.create_main_layout()
        self.create_calendar_area()
        self.create_remarks_area()
        self.create_action_buttons_area()
        self.create_recent_records_area()
        self.create_status_bar()

        self.update_calendar_display_dates()
        self.update_recent_records_list()
        self.update_status_bar_tick()

    def setup_styles_and_theme(self):
        self.root.configure(bg=APP_BG_COLOR)
        try:
            self.root.attributes('-alpha', WINDOW_TRANSPARENCY)
        except tk.TclError:
            print("当前平台不支持窗口透明度。")

        self.style = ttk.Style()
        try:
            available_themes = self.style.theme_names()
            if 'clam' in available_themes:
                self.style.theme_use('clam')
            elif 'alt' in available_themes:
                self.style.theme_use('alt')
        except tk.TclError:
            pass

        self.style.configure("TFrame", background=APP_BG_COLOR)
        self.style.configure("TLabel", background=APP_BG_COLOR, foreground=TEXT_COLOR, font=('Arial', 10))
        self.style.configure("TLabelframe", background=APP_BG_COLOR, bordercolor="grey")
        self.style.configure("TLabelframe.Label", background=APP_BG_COLOR, foreground=TEXT_COLOR, font=('Arial', 10, 'bold'))
        self.style.configure("TButton", font=('Arial', 10), padding=5)
        self.style.configure("Treeview", font=('Arial', 9), rowheight=25, background="#E6F3FF")  # Light blue for recent records
        self.style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        self.style.configure("Status.TLabel", background=APP_BG_COLOR, foreground=TEXT_COLOR, font=('Arial', 9))
        self.style.configure("Pink.Date", background=HIGHLIGHT_COLOR, foreground="black")
        self.style.configure("Green.Date", background=MEETING_HIGHLIGHT_COLOR, foreground="black")

    def create_main_layout(self):
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.left_panel = ttk.Frame(self.main_frame)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.right_panel = ttk.Frame(self.main_frame)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y, expand=False)

    def create_calendar_area(self):
        calendar_outer_frame = ttk.LabelFrame(self.left_panel, text="双日历视图", padding=10)
        calendar_outer_frame.pack(fill=tk.BOTH, expand=True, pady=(0,10))
        
        nav_frame = ttk.Frame(calendar_outer_frame)
        nav_frame.pack(pady=5)
        ttk.Button(nav_frame, text="<< 上个月", command=self.prev_month_pair).pack(side=tk.LEFT, padx=10)
        ttk.Button(nav_frame, text="下个月 >>", command=self.next_month_pair).pack(side=tk.RIGHT, padx=10)

        calendars_frame = ttk.Frame(calendar_outer_frame)
        calendars_frame.pack(fill=tk.BOTH, expand=True)

        self.cal1_frame = ttk.Frame(calendars_frame)
        self.cal1_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.cal1_month_year_label = ttk.Label(self.cal1_frame, text="", font=('Arial', 12, 'bold'))
        self.cal1_month_year_label.pack(pady=(0,5))
        self.cal1 = Calendar(self.cal1_frame, selectmode='day', date_pattern='yyyy-mm-dd',
                             font="Arial 9", borderwidth=1, showweeknumbers=False,
                             background=APP_BG_COLOR, foreground=TEXT_COLOR,
                             headersbackground=APP_BG_COLOR, headersforeground=TEXT_COLOR,
                             normalbackground="white", normalforeground="black",
                             weekendbackground="white", weekendforeground="black",
                             othermonthbackground="lightgrey", othermonthforeground="darkgrey",
                             othermonthwebackground="lightgrey", othermonthweforeground="darkgrey",
                             selectbackground="#77A2D9", selectforeground="white"
                            )
        self.cal1.pack(fill=tk.BOTH, expand=True)
        self.cal1.bind("<<CalendarSelected>>", lambda e: self.on_calendar_date_selected(self.cal1))

        self.cal2_frame = ttk.Frame(calendars_frame)
        self.cal2_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        self.cal2_month_year_label = ttk.Label(self.cal2_frame, text="", font=('Arial', 12, 'bold'))
        self.cal2_month_year_label.pack(pady=(0,5))
        self.cal2 = Calendar(self.cal2_frame, selectmode='day', date_pattern='yyyy-mm-dd',
                             font="Arial 9", borderwidth=1, showweeknumbers=False,
                             background=APP_BG_COLOR, foreground=TEXT_COLOR,
                             headersbackground=APP_BG_COLOR, headersforeground=TEXT_COLOR,
                             normalbackground="white", normalforeground="black",
                             weekendbackground="white", weekendforeground="black",
                             othermonthbackground="lightgrey", othermonthforeground="darkgrey",
                             othermonthwebackground="lightgrey", othermonthweforeground="darkgrey",
                             selectbackground="#77A2D9", selectforeground="white"
                            )
        self.cal2.pack(fill=tk.BOTH, expand=True)
        self.cal2.bind("<<CalendarSelected>>", lambda e: self.on_calendar_date_selected(self.cal2))

        for cal in [self.cal1, self.cal2]:
            cal.tag_config('vacation_highlight', background=HIGHLIGHT_COLOR, foreground='black')
            cal.tag_config('meeting_highlight', background=MEETING_HIGHLIGHT_COLOR, foreground='black')

    def create_remarks_area(self):
        remarks_frame = ttk.LabelFrame(self.left_panel, text="休假备注信息", padding=10)
        remarks_frame.pack(fill=tk.X, pady=(0,10))

        self.remarks_info_label = ttk.Label(remarks_frame, text="点击日历中的日期进行操作。", wraplength=350)
        self.remarks_info_label.pack(pady=5, fill=tk.X)

        remark_input_frame = ttk.Frame(remarks_frame)
        remark_input_frame.pack(fill=tk.X)
        
        ttk.Label(remark_input_frame, text="类型:").pack(side=tk.LEFT, padx=(0,5))
        self.remark_options = ["年休假", "家长会", "倒休", "其他"]
        self.remark_type_var = tk.StringVar(value=self.remark_options[0])
        self.remark_menu = ttk.OptionMenu(remark_input_frame, self.remark_type_var, self.remark_options[0], *self.remark_options, command=self.on_remark_type_changed)
        self.remark_menu.pack(side=tk.LEFT, padx=(0,10))

        self.other_remark_entry = ttk.Entry(remark_input_frame, width=20, state=tk.DISABLED)
        self.other_remark_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.add_vacation_button = ttk.Button(remarks_frame, text="添加选中日期/范围为休假", command=self.process_add_vacation_from_selection)
        self.add_vacation_button.pack(pady=5, fill=tk.X)

    def create_action_buttons_area(self):
        action_frame = ttk.LabelFrame(self.right_panel, text="操作", padding=10)
        action_frame.pack(fill=tk.X, pady=(0,10))

        self.range_select_checkbutton = ttk.Checkbutton(action_frame, text="启用日期范围选择", variable=self.is_range_select_mode, command=self.toggle_range_select_mode)
        self.range_select_checkbutton.pack(pady=5, anchor=tk.W)
        
        self.delete_button = ttk.Button(action_frame, text="删除所选休假", command=self.delete_selected_vacation, state=tk.DISABLED)
        self.delete_button.pack(pady=5, fill=tk.X)

        self.export_button = ttk.Button(action_frame, text="导出休假数据到Excel", command=self.export_data_to_excel)
        self.export_button.pack(pady=5, fill=tk.X)

    def create_recent_records_area(self):
        recent_frame = ttk.LabelFrame(self.right_panel, text="最近记录 (滚动)", padding=10)
        recent_frame.pack(fill=tk.BOTH, expand=True)

        # Vacation records
        vacation_frame = ttk.Frame(recent_frame)
        vacation_frame.pack(fill=tk.X, pady=5)
        ttk.Label(vacation_frame, text="最近一年休假:").pack(side=tk.LEFT)
        cols_vacation = ("日期", "备注")
        self.recent_vacations_tree = ttk.Treeview(vacation_frame, columns=cols_vacation, show='headings', height=5)
        self.recent_vacations_tree.column("日期", width=100, anchor=tk.W)
        self.recent_vacations_tree.column("备注", width=180, anchor=tk.W)
        for col in cols_vacation:
            self.recent_vacations_tree.heading(col, text=col)
        self.recent_vacations_tree.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # Meeting records
        meeting_frame = ttk.Frame(recent_frame)
        meeting_frame.pack(fill=tk.X, pady=5)
        ttk.Label(meeting_frame, text="最近会议:").pack(side=tk.LEFT)
        cols_meeting = ("日期", "会议内容")
        self.recent_meetings_tree = ttk.Treeview(meeting_frame, columns=cols_meeting, show='headings', height=5)
        self.recent_meetings_tree.column("日期", width=100, anchor=tk.W)
        self.recent_meetings_tree.column("会议内容", width=180, anchor=tk.W)
        for col in cols_meeting:
            self.recent_meetings_tree.heading(col, text=col)
        self.recent_meetings_tree.pack(side=tk.RIGHT, fill=tk.X, expand=True)

    def create_status_bar(self):
        status_bar_frame = ttk.Frame(self.root, relief=tk.SUNKEN, padding=(5,2))
        status_bar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        status_bar_frame.configure(style="Status.TFrame")

        self.time_label = ttk.Label(status_bar_frame, text="时间: --", style="Status.TLabel")
        self.time_label.pack(side=tk.LEFT, padx=5)
        self.mem_label = ttk.Label(status_bar_frame, text="内存: --%", style="Status.TLabel")
        self.mem_label.pack(side=tk.LEFT, padx=5)
        self.net_label = ttk.Label(status_bar_frame, text="网络: ↓ -- KB/s ↑ -- KB/s", style="Status.TLabel")
        self.net_label.pack(side=tk.LEFT, padx=5)

    def update_calendar_display_dates(self):
        y1, m1 = self.current_display_year, self.current_display_month
        self.cal1.display_date = datetime.date(y1, m1, 1)
        self.cal1_month_year_label.config(text=f"{y1}年 {m1:02d}月")

        y2, m2 = y1, m1 + 1
        if m2 > 12:
            m2 = 1
            y2 += 1
        self.cal2.display_date = datetime.date(y2, m2, 1)
        self.cal2_month_year_label.config(text=f"{y2}年 {m2:02d}月")
        
        self.load_and_highlight_vacations_and_meetings()

    def prev_month_pair(self):
        self.current_display_month -= 1
        if self.current_display_month < 1:
            self.current_display_month = 12
            self.current_display_year -= 1
        self.update_calendar_display_dates()

    def next_month_pair(self):
        self.current_display_month += 1
        if self.current_display_month > 12:
            self.current_display_month = 1
            self.current_display_year += 1
        self.update_calendar_display_dates()

    def load_and_highlight_vacations_and_meetings(self):
        for cal in [self.cal1, self.cal2]:
            cal.calevent_remove('all')

        y1, m1 = self.cal1.display_date.year, self.cal1.display_date.month
        y2, m2 = self.cal2.display_date.year, self.cal2.display_date.month

        start_date_display = datetime.date(y1, m1, 1)
        if m2 == 12:
            end_date_display = datetime.date(y2, m2, 31)
        else:
            end_date_display = datetime.date(y2, m2 + 1, 1) - datetime.timedelta(days=1)
        
        vacations_in_view = self.db.get_vacations_in_range(start_date_display, end_date_display)
        if vacations_in_view is None: vacations_in_view = []

        meetings_in_view = self.db.get_meetings_in_range(start_date_display, end_date_display)
        if meetings_in_view is None: meetings_in_view = []

        for vac_date, remarks in vacations_in_view:
            for cal in [self.cal1, self.cal2]:
                if vac_date.year == cal.display_date.year and vac_date.month == cal.display_date.month:
                    cal.calevent_create(vac_date, remarks if remarks else "休假", 'vacation_highlight')

        for meet_date, content in meetings_in_view:
            for cal in [self.cal1, self.cal2]:
                if meet_date.year == cal.display_date.year and meet_date.month == cal.display_date.month:
                    cal.calevent_create(meet_date, content[:20] + "..." if content and len(content) > 20 else content or "会议", 'meeting_highlight')

        if hasattr(self, 'temp_highlight_ids_cal1'):
            for event_id in self.temp_highlight_ids_cal1: self.cal1.calevent_remove(event_id, 'temp_range_select')
            self.temp_highlight_ids_cal1 = []
        if hasattr(self, 'temp_highlight_ids_cal2'):
            for event_id in self.temp_highlight_ids_cal2: self.cal2.calevent_remove(event_id, 'temp_range_select')
            self.temp_highlight_ids_cal2 = []

    def on_calendar_date_selected(self, calendar_widget):
        selected_date_str = calendar_widget.get_date()
        self.selected_single_date_obj = datetime.datetime.strptime(selected_date_str, '%Y-%m-%d').date()

        if self.is_range_select_mode.get():
            if not self.range_start_date_obj:
                self.range_start_date_obj = self.selected_single_date_obj
                self.remarks_info_label.config(text=f"范围开始: {self.range_start_date_obj}. 请选择结束日期或点击添加。")
            else:
                self.remarks_info_label.config(text=f"范围: {self.range_start_date_obj} 到 {self.selected_single_date_obj}. 请确认备注类型并添加。")
        else:
            vacation_info = self.db.get_vacation_by_date(self.selected_single_date_obj)
            meeting_info = self.db.get_meeting_by_date(self.selected_single_date_obj)
            if vacation_info:
                remarks = vacation_info[0]
                self.remarks_info_label.config(text=f"休假备注 ({selected_date_str}): {remarks}")
                self.delete_button.config(state=tk.NORMAL)
            elif meeting_info:
                content = meeting_info[0]
                self.remarks_info_label.config(text=f"会议记录 ({selected_date_str}): {content[:50]}{'...' if len(content) > 50 else ''}")
                self.delete_button.config(state=tk.DISABLED)
            else:
                self.remarks_info_label.config(text=f"{selected_date_str}: 非休假日/无会议。点击以选择操作。")
                self.delete_button.config(state=tk.DISABLED)
            self.show_context_menu(calendar_widget)

    def show_context_menu(self, calendar_widget):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="新建休假", command=lambda: self.process_add_vacation_from_selection())
        menu.add_command(label="新建会议", command=lambda: self.open_meeting_dialog(calendar_widget.get_date()))
        menu.post(self.root.winfo_pointerx(), self.root.winfo_pointery())

    def open_meeting_dialog(self, selected_date_str):
        date_obj = datetime.datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        meeting_info = self.db.get_meeting_by_date(date_obj)
        existing_content = meeting_info[0] if meeting_info else ""

        dialog = tk.Toplevel(self.root)
        dialog.title(f"会议记录 - {selected_date_str}")
        dialog.geometry("400x300")
        dialog.configure(bg=APP_BG_COLOR)
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="会议内容:", background=APP_BG_COLOR, foreground=TEXT_COLOR).pack(pady=5)
        content_text = tk.Text(dialog, height=10, width=40, bg="white", fg="black")
        content_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        content_text.insert(tk.END, existing_content)

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        def submit_meeting():
            content = content_text.get("1.0", tk.END).strip()
            if not content:
                messagebox.showwarning("输入错误", "会议内容不能为空。", parent=dialog)
                return
            if self.db.add_meeting(date_obj, content):
                messagebox.showinfo("成功", f"已为 {selected_date_str} 添加/更新会议记录。", parent=dialog)
                self.load_and_highlight_vacations_and_meetings()
                self.update_recent_records_list()
                dialog.destroy()
            else:
                messagebox.showerror("失败", f"无法为 {selected_date_str} 添加/更新会议记录。", parent=dialog)

        def delete_meeting():
            if not meeting_info:
                messagebox.showerror("错误", f"日期 {selected_date_str} 没有会议记录可删除。", parent=dialog)
                return
            if messagebox.askyesno("确认删除", f"确定要删除 {selected_date_str} 的会议记录吗？", parent=dialog):
                if self.db.delete_meeting(date_obj):
                    messagebox.showinfo("成功", f"已删除 {selected_date_str} 的会议记录。", parent=dialog)
                    self.load_and_highlight_vacations_and_meetings()
                    self.update_recent_records_list()
                    dialog.destroy()
                else:
                    messagebox.showerror("失败", f"删除 {selected_date_str} 的会议记录失败。", parent=dialog)

        ttk.Button(button_frame, text="确定提交", command=submit_meeting).pack(side=tk.LEFT, padx=5)
        if meeting_info:
            ttk.Button(button_frame, text="删除会议", command=delete_meeting).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def process_add_vacation_from_selection(self):
        final_remarks = self.remark_type_var.get()
        if final_remarks == "其他":
            final_remarks = self.other_remark_entry.get().strip()
            if not final_remarks:
                messagebox.showwarning("备注错误", "选择“其他”类型时，备注内容不能为空。")
                return
        
        dates_to_add = []
        if self.is_range_select_mode.get() and self.range_start_date_obj and self.selected_single_date_obj:
            start = min(self.range_start_date_obj, self.selected_single_date_obj)
            end = max(self.range_start_date_obj, self.selected_single_date_obj)
            current = start
            while current <= end:
                dates_to_add.append(current)
                current += datetime.timedelta(days=1)
            self.range_start_date_obj = None
            self.remarks_info_label.config(text="范围已处理。可开始新的单选或范围选择。")
        elif self.selected_single_date_obj:
            if self.db.get_vacation_by_date(self.selected_single_date_obj):
                messagebox.showinfo("提示", f"日期 {self.selected_single_date_obj} 已是休假日。如需修改请先删除。")
                return
            dates_to_add.append(self.selected_single_date_obj)
        else:
            messagebox.showwarning("选择错误", "请先在日历中选择一个日期或一个日期范围。")
            return

        if not dates_to_add:
            messagebox.showwarning("无日期", "没有有效日期被选中用于添加休假。")
            return

        added_count = 0
        failed_dates = []
        for date_obj in dates_to_add:
            if self.db.add_vacation(date_obj, final_remarks):
                added_count += 1
            else:
                if not self.db.get_vacation_by_date(date_obj):
                    failed_dates.append(str(date_obj))

        if added_count > 0:
            messagebox.showinfo("成功", f"成功为 {added_count} 个日期添加了休假备注: {final_remarks}")
        if failed_dates:
            messagebox.showerror("部分失败", f"以下日期添加失败 (可能数据库错误):\n{', '.join(failed_dates)}")
        
        self.load_and_highlight_vacations_and_meetings()
        self.update_recent_records_list()

    def on_remark_type_changed(self, selected_type=None):
        if self.remark_type_var.get() == "其他":
            self.other_remark_entry.config(state=tk.NORMAL)
        else:
            self.other_remark_entry.config(state=tk.DISABLED)
            self.other_remark_entry.delete(0, tk.END)

    def toggle_range_select_mode(self):
        self.range_start_date_obj = None
        if self.is_range_select_mode.get():
            self.remarks_info_label.config(text="范围选择已启用：请先点选开始日期。")
        else:
            self.remarks_info_label.config(text="点击日历中的日期进行操作。")
            self.load_and_highlight_vacations_and_meetings()

    def delete_selected_vacation(self):
        if not self.selected_single_date_obj:
            messagebox.showwarning("选择错误", "请先在日历中选择一个已标记的休假日期。")
            return

        vacation_info = self.db.get_vacation_by_date(self.selected_single_date_obj)
        if not vacation_info:
            messagebox.showerror("错误", f"日期 {self.selected_single_date_obj} 当前不是休假日。")
            self.delete_button.config(state=tk.DISABLED)
            return

        reason = simpledialog.askstring("删除原因", f"请输入删除日期 {self.selected_single_date_obj} 的原因 (可选):", parent=self.root)

        if self.db.delete_vacation(self.selected_single_date_obj, reason if reason is not None else ""):
            messagebox.showinfo("成功", f"已删除休假日期: {self.selected_single_date_obj}")
            self.load_and_highlight_vacations_and_meetings()
            self.update_recent_records_list()
            self.remarks_info_label.config(text="点击日历中的日期进行操作。")
            self.delete_button.config(state=tk.DISABLED)
            self.selected_single_date_obj = None
        else:
            messagebox.showerror("删除失败", f"删除休假日期 {self.selected_single_date_obj} 失败。")

    def update_recent_records_list(self):
        # Update vacation records
        for i in self.recent_vacations_tree.get_children():
            self.recent_vacations_tree.delete(i)
        recent_vacations = self.db.get_recent_vacations()
        for vac_date_str, remarks in recent_vacations:
            self.recent_vacations_tree.insert("", tk.END, values=(vac_date_str, remarks))

        # Update meeting records
        for i in self.recent_meetings_tree.get_children():
            self.recent_meetings_tree.delete(i)
        recent_meetings = self.db.get_recent_meetings()
        for meet_date_str, content in recent_meetings:
            self.recent_meetings_tree.insert("", tk.END, values=(meet_date_str, content[:50] + "..." if content and len(content) > 50 else content))

    def export_data_to_excel(self):
        all_vacations = self.db.get_all_vacations_for_export()
        if not all_vacations:
            messagebox.showinfo("无数据", "没有休假数据可以导出。")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="导出休假数据为Excel"
        )
        if not filepath:
            return

        try:
            excel_exporter.export_data_to_excel(all_vacations, filepath)
            messagebox.showinfo("成功", f"休假数据已成功导出到\n{filepath}")
        except Exception as e:
            messagebox.showerror("导出失败", f"导出Excel失败: {e}")

    def update_status_bar_tick(self):
        current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=f"时间: {current_time_str}")

        mem_usage = self.sys_mon.get_memory_usage()
        self.mem_label.config(text=f"内存: {mem_usage:.1f}%")

        down_speed, up_speed = self.sys_mon.get_network_speed()
        self.net_label.config(text=f"网络: ↓{down_speed:.1f}KB/s ↑{up_speed:.1f}KB/s")

        self.root.after(1000, self.update_status_bar_tick)

if __name__ == '__main__':
    root = tk.Tk()
    try:
        app = VacationApp(root)
        if hasattr(app, 'db'):
            root.mainloop()
        else:
            print("应用程序初始化失败，窗口未启动。")
            if root.winfo_exists():
                root.destroy()
    except Exception as e:
        print(f"发生未捕获的严重错误: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("严重错误", f"应用程序遇到严重错误，即将关闭。\n详情: {e}")
        if root.winfo_exists():
            root.destroy()
