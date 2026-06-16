import re

file_path = "src/interfaces/slack/commands.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Fix leftover _get_services() and svcs calls
# Some lines have `svcs, session = await _get_services()` which wasn't replaced because of missing `async with session:` block below it, or different spacing.

content = re.sub(r"[ \t]*svcs,.*?await _get_services\(\)\n", "", content)
content = re.sub(r"await svcs\[\"excel\"\]", "await uow.valuelist_svc", content)

# If `container = get_container()` is missing in functions that used to have `_get_services`, we should inject it.
# Instead of regex, I'll do a simple string replacement for known commands that were broken.

def ensure_container(func_name, code):
    pattern = f"(    @app\\.command\\(\"{func_name}\"\\)\n.*?await ack\\(\\)\n)"
    replacement = r"\1        container = get_container()\n"
    if "container = get_container()" not in re.search(f"(    @app\\.command\\(\"{func_name}\"\\)\n.*?)(    @app\\.command|\\Z)", code, re.DOTALL).group(1):
         return re.sub(pattern, replacement, code, count=1, flags=re.DOTALL)
    return code

for cmd in ["/mis-tareas", "/bitacora", "/avance", "/evidencia", "/gantt", "/editar", "/todas-las-tareas"]:
    content = ensure_container(cmd, content)


# 2. Refactor /reporte to use background task
report_old = """    @app.command("/reporte")
    async def handle_reporte_command(ack, say):
        await ack()
        container = get_container()
        async with container.uow() as uow:
            summary = await uow.report_svc.generate_daily_summary(
                default_team_id, default_channel_id
            )
        await say(f"{summary}\\n\\n")"""

report_new = """    @app.command("/reporte")
    async def handle_reporte_command(ack, say, client, command):
        await ack("⏳ *Generando reporte diario con IA...* Esto tomará unos segundos.")
        
        async def background_report():
            try:
                container = get_container()
                async with container.uow() as uow:
                    summary = await uow.report_svc.generate_daily_summary(
                        default_team_id, default_channel_id
                    )
                await client.chat_postMessage(channel=command["channel_id"], text=f"✅ *Reporte Diario:*\\n\\n{summary}")
            except Exception as e:
                await client.chat_postMessage(channel=command["channel_id"], text=f"❌ *Error generando el reporte:* {str(e)}")

        import asyncio
        asyncio.create_task(background_report())"""

content = content.replace(report_old, report_new)

# 3. Refactor /github to use background task
github_old = """    @app.command("/github")
    async def handle_github_command(ack, say):
        await ack()
        if not settings.github_default_org:
            await say("❌ GitHub sync no configurado (falta GITHUB_DEFAULT_ORG).")
            return
        await say("⚙️ *Sincronizando Pull Requests desde GitHub...*")
        container = get_container()
        async with container.uow() as uow:
            await uow.github_svc.sync_pull_requests(
                default_team_id,
                settings.github_default_org,
                [settings.github_default_org],
            )
        await say("✅ Sincronización completada.")"""

github_new = """    @app.command("/github")
    async def handle_github_command(ack, say, client, command):
        if not settings.github_default_org:
            await ack("❌ GitHub sync no configurado (falta GITHUB_DEFAULT_ORG).")
            return
            
        await ack("⚙️ *Sincronizando Pull Requests desde GitHub...*")
        
        async def background_github():
            try:
                container = get_container()
                async with container.uow() as uow:
                    await uow.github_svc.sync_pull_requests(
                        default_team_id,
                        settings.github_default_org,
                        [settings.github_default_org],
                    )
                await client.chat_postMessage(channel=command["channel_id"], text="✅ Sincronización completada.")
            except Exception as e:
                await client.chat_postMessage(channel=command["channel_id"], text=f"❌ *Error sincronizando:* {str(e)}")

        import asyncio
        asyncio.create_task(background_github())"""

content = content.replace(github_old, github_new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("commands fixed.")
