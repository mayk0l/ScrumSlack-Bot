import asyncio
from src.application.valuelist_excel_service import ValuelistExcelService

async def main():
    svc = ValuelistExcelService('project_tracking.xlsx')
    print(await svc.get_all_active_tasks())

asyncio.run(main())
