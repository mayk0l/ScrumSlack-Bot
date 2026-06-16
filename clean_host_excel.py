import openpyxl
import shutil

# Start fresh
shutil.copy("excel/Bitacora-Rentabilidad-Valuelist.xlsx", "project_tracking.xlsx")

wb = openpyxl.load_workbook("project_tracking.xlsx")

# 1. Clean Planificación
ws = wb["Planificación"]
max_r = ws.max_row
if max_r >= 2:
    ws.delete_rows(2, max_r)

# 2. Clean Administración
ws = wb["Administración"]
max_r = ws.max_row
if max_r >= 2:
    ws.delete_rows(2, max_r)

# 3. Clean Evidencias
if "Evidencias" in wb.sheetnames:
    ws = wb["Evidencias"]
    max_r = ws.max_row
    if max_r >= 2:
        ws.delete_rows(2, max_r)

# 4. Clean Gantt COMPLETELY below headers
if "Gantt" in wb.sheetnames:
    ws = wb["Gantt"]
    max_r = ws.max_row
    if max_r >= 3:
        ws.delete_rows(3, max_r)

# 5. Clean Bitácora completely
ws = wb["Bitácora"]

# Clear descriptions in rows 2-8
for r in range(2, 9):
    ws.cell(row=r, column=3, value="")

# Delete everything below row 8
max_r = ws.max_row
if max_r >= 9:
    ws.delete_rows(9, max_r)

wb.save("project_tracking.xlsx")
print("Cleaned project_tracking.xlsx, wiped Gantt rows 3+.")
