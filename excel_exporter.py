import openpyxl
from openpyxl.styles import Font, Alignment

def export_data_to_excel(vacation_data, filepath):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "休假记录"

    headers = ["休假日期", "备注", "记录创建时间"]
    sheet.append(headers)

    header_font = Font(bold=True)
    for col_num, header_title in enumerate(headers, 1):
        cell = sheet.cell(row=1, column=col_num)
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    # vacation_data 应该是 [(date_str, remarks_str, created_at_str), ...]
    for record in vacation_data:
        sheet.append(record)

    for col in sheet.columns:
        max_length = 0
        column_letter = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2) if max_length > 0 else 15 # 最小宽度
        sheet.column_dimensions[column_letter].width = adjusted_width

    workbook.save(filepath)
