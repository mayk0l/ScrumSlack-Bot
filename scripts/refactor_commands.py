import os
import re

file_path = "src/interfaces/slack/commands.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add get_container import
content = re.sub(
    r"from src\.config import settings",
    "from src.config import settings\nfrom src.container import get_container",
    content
)

# 2. Remove _get_services definition
# It starts at `async def _get_services():` and ends before `@app.command`
content = re.sub(
    r"    async def _get_services\(\):.*?    @app.command",
    "    @app.command",
    content,
    flags=re.DOTALL
)

# 3. Remove `maker = services["session_maker"]` and `github_client = services["github_client"]`
content = re.sub(r"    maker = services\[\"session_maker\"\]\n", "", content)
content = re.sub(r"    github_client = services\[\"github_client\"\]\n", "", content)

# 4. Replace usages
# Pattern:
#         svcs, session = await _get_services()
#         async with session:
#             data = await svcs["X"].method(...)
#
# Becomes:
#         container = get_container()
#         async with container.uow() as uow:
#             data = await uow.X_svc.method(...)

content = re.sub(
    r"[ \t]*svcs, session = await _get_services\(\)\n[ \t]*async with session:",
    "        container = get_container()\n        async with container.uow() as uow:",
    content
)

# Replace dictionary access with uow attributes
replacements = {
    'svcs["risk"]': 'uow.risk_svc',
    'svcs["standup"]': 'uow.standup_svc',
    'svcs["sprint"]': 'uow.sprint_svc',
    'svcs["report"]': 'uow.report_svc',
    'svcs["github"]': 'uow.github_svc',
    'svcs["valuelist"]': 'uow.valuelist_svc',
    'svcs["member"]': 'uow.member_repo',
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("commands.py refactored.")
