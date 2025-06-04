import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
import datetime

def format_value(value):
    if isinstance(value, datetime.datetime) or isinstance(value, datetime.date):
        return value.strftime('%Y-%m-%d %H:%M:%S') if isinstance(value, datetime.datetime) else value.strftime('%Y-%m-%d')
    if value is None:
        return ""
    if isinstance(value, bool):
        return "是" if value else "否" # Yes/No for boolean
    return str(value)

def export_data_to_excel(vacations_data, meetings_data, filepath):
    workbook = openpyxl.Workbook()

    # Remove default sheet
    if "Sheet" in workbook.sheetnames:
        std = workbook["Sheet"]
        workbook.remove(std)

    # Define some styles
    header_font = Font(bold=True, color="FFFFFF") # White text
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid") # Blue fill
    center_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left_alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    thin_border = Border(left=Side(style='thin'),
                         right=Side(style='thin'),
                         top=Side(style='thin'),
                         bottom=Side(style='thin'))

    # Create Vacations Sheet
    ws_vacations = workbook.create_sheet(title="休假记录 (Vacations)")
    vac_headers = ["日期 (Date)", "类型 (Type)", "备注 (Remarks)", "是否取消 (Cancelled)", "取消原因 (Deletion Reason)", "记录时间 (Created At)"]
    ws_vacations.append(vac_headers)
    for col_num, header_title in enumerate(vac_headers, 1):
        cell = ws_vacations.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment
        ws_vacations.column_dimensions[get_column_letter(col_num)].width = 20 if col_num != 3 else 40 # Remarks wider

    if vacations_data:
        for row_data in vacations_data:
            # Ensure order matches headers: vacation_date, type, remarks, cancelled, deletion_reason, created_at
            # DB returns dicts, so access by key
            formatted_row = [
                format_value(row_data.get('vacation_date')),
                format_value(row_data.get('type')),
                format_value(row_data.get('remarks')),
                format_value(row_data.get('cancelled')),
                format_value(row_data.get('deletion_reason')),
                format_value(row_data.get('created_at'))
            ]
            ws_vacations.append(formatted_row)

    for row in ws_vacations.iter_rows(min_row=1, max_row=ws_vacations.max_row, min_col=1, max_col=ws_vacations.max_column):
        for cell in row:
            cell.border = thin_border
            if cell.row > 1 : # Data rows
                 cell.alignment = left_alignment


    # Create Meetings Sheet
    ws_meetings = workbook.create_sheet(title="会议记录 (Meetings)")
    meet_headers = ["日期 (Date)", "会议内容 (Content)", "是否取消 (Cancelled)", "取消原因 (Deletion Reason)", "记录时间 (Created At)"]
    ws_meetings.append(meet_headers)
    for col_num, header_title in enumerate(meet_headers, 1):
        cell = ws_meetings.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment
        ws_meetings.column_dimensions[get_column_letter(col_num)].width = 20 if col_num != 2 else 50 # Content wider

    if meetings_data:
        for row_data in meetings_data:
            # Order: meeting_date, content, cancelled, deletion_reason, created_at
            formatted_row = [
                format_value(row_data.get('meeting_date')),
                format_value(row_data.get('content')),
                format_value(row_data.get('cancelled')),
                format_value(row_data.get('deletion_reason')),
                format_value(row_data.get('created_at'))
            ]
            ws_meetings.append(formatted_row)

    for row in ws_meetings.iter_rows(min_row=1, max_row=ws_meetings.max_row, min_col=1, max_col=ws_meetings.max_column):
        for cell in row:
            cell.border = thin_border
            if cell.row > 1 : # Data rows
                 cell.alignment = left_alignment

    workbook.save(filepath)
    return True

def generate_txt_content(vacations_data, meetings_data):
    txt_lines = []
    txt_lines.append("休假记录 (Vacations Data)")
    txt_lines.append("="*30)
    vac_headers = ["日期", "类型", "备注", "是否取消", "取消原因", "记录时间"]
    txt_lines.append("	".join(vac_headers))
    if vacations_data:
        for row in vacations_data:
            formatted_row = [
                format_value(row.get('vacation_date')), format_value(row.get('type')),
                format_value(row.get('remarks')), format_value(row.get('cancelled')),
                format_value(row.get('deletion_reason')), format_value(row.get('created_at'))
            ]
            txt_lines.append("	".join(formatted_row))
    else:
        txt_lines.append("无休假数据 (No vacation data).")

    txt_lines.append("\n\n会议记录 (Meetings Data)") # Corrected newline handling
    txt_lines.append("="*30)
    meet_headers = ["日期", "会议内容", "是否取消", "取消原因", "记录时间"]
    txt_lines.append("	".join(meet_headers))
    if meetings_data:
        for row in meetings_data:
            formatted_row = [
                format_value(row.get('meeting_date')), format_value(row.get('content')),
                format_value(row.get('cancelled')), format_value(row.get('deletion_reason')),
                format_value(row.get('created_at'))
            ]
            txt_lines.append("	".join(formatted_row))
    else:
        txt_lines.append("无会议数据 (No meeting data).")

    return "\n".join(txt_lines)
