import openpyxl

wb = openpyxl.load_workbook("project_tracking.xlsx", data_only=True)
ws = wb["Bitácora"]

for i in range(30, 60):
    row_vals = [ws.cell(row=i, column=c).value for c in range(1, 5)]
    print(f"Row {i}: {row_vals}")
