import os
import re

file_path = "src/interfaces/slack/modals.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace manual standup service instantiation
standup_pattern = r"""    async def _get_standup_service\(\):
        session = maker\(\)
        return StandupService\(
            session_repo=StandupSessionRepositoryImpl\(session\),
            response_repo=StandupResponseRepositoryImpl\(session\),
            member_repo=MemberRepositoryImpl\(session\),
        \), session"""

content = re.sub(standup_pattern, "", content)

# Also remove maker = services["session_maker"]
content = re.sub(r'    maker = services\["session_maker"\]\n\n', '', content)

# Fix standup_submission handler
content = re.sub(
    r"[ \t]*svc, session = await _get_standup_service\(\)\n[ \t]*async with session:",
    "        from src.container import get_container\n        container = get_container()\n        async with container.uow() as uow:",
    content
)
content = re.sub(r"await svc\.submit_response", "await uow.standup_svc.submit_response", content)

# Fix ValuelistExcelService instantiations
# Replace:
#         from src.application.valuelist_excel_service import ValuelistExcelService
#         from src.config import settings
#         valuelist_svc = ValuelistExcelService(settings.excel_file_path)
valuelist_instantiation = r"[ \t]*from src\.application\.valuelist_excel_service import ValuelistExcelService\n[ \t]*from src\.config import settings\n[ \t]*valuelist_svc = ValuelistExcelService\(settings\.excel_file_path\)\n"
content = re.sub(
    valuelist_instantiation,
    "        from src.container import get_container\n        valuelist_svc = get_container().valuelist_svc\n",
    content
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("modals.py refactored.")
